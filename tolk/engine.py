"""Rules to SQL, run to fixpoint. Identifiers are fixed column names and generated aliases; every value is a bound parameter."""

from tolk import lf, store
from tolk.lf import Atom, Const, Var

Statement = tuple[str, tuple]


def run(db, ctx: str = "world") -> int:
    """Run every rule until a round adds nothing. Returns the number of facts added."""
    total = 0
    prev = store.current_round(db)
    while True:
        rnd = prev + 1
        before = db.execute("SELECT COUNT(*) FROM fact").fetchone()[0]
        for rule_id, text, ran in db.execute("SELECT id, lf, ran FROM rule ORDER BY id").fetchall():
            rule = lf.decode_rule(text)
            for sql, params in rule_sql(rule, rule_id, ctx, prev if ran is not None else None, rnd):
                db.execute(sql, params)
            db.execute("UPDATE rule SET ran = ? WHERE id = ?", (rnd, rule_id))
        added = db.execute("SELECT COUNT(*) FROM fact").fetchone()[0] - before
        if added == 0:
            record_conflicts(db)
            return total
        total += added
        prev = rnd


def record_conflicts(db) -> None:
    """A positive and a negative fact that clash get a conflict row, once one of them was derived."""
    db.execute(
        "INSERT INTO conflict(positive_fact, negative_fact) "
        "SELECT p.id, n.id FROM fact AS p JOIN fact AS n "
        "ON n.pred = p.pred AND n.ctx = p.ctx AND n.a1 = p.a1 AND n.a2 = p.a2 AND (n.a0 = p.a0 OR n.a0 = '') "
        "WHERE p.positive = 1 AND n.positive = 0 "
        "AND (EXISTS (SELECT 1 FROM why w WHERE w.fact = p.id AND w.rule IS NOT NULL) "
        "     OR EXISTS (SELECT 1 FROM why w WHERE w.fact = n.id AND w.rule IS NOT NULL)) "
        "AND NOT EXISTS (SELECT 1 FROM conflict c WHERE c.positive_fact = p.id AND c.negative_fact = n.id)"
    )


def check(db, rule: lf.Rule) -> lf.Refusal | None:
    """A rule is stored only if its negated variables are bound by a positive atom and no negated predicate depends on its head."""
    positive_vars = {t for a in rule.body if a.positive for t in a.args if isinstance(t, Var)}
    for a in rule.body:
        if a.positive:
            continue
        for t in a.args:
            if isinstance(t, Var) and not t.event and t not in positive_vars:
                return lf.Refusal("UNSAFE_NEGATION", t.key)
    rules = [lf.decode_rule(text) for (text,) in db.execute("SELECT lf FROM rule")] + [rule]
    for a in rule.body:
        if not a.positive and _reaches(rules, a.pred, {h.pred for h in rule.head}):
            return lf.Refusal("UNSTRATIFIED", a.pred)
    return None


def _reaches(rules: list[lf.Rule], start: str, targets: set[str]) -> bool:
    seen, todo = set(), [start]
    while todo:
        pred = todo.pop()
        if pred in targets:
            return True
        if pred in seen:
            continue
        seen.add(pred)
        for r in rules:
            if any(h.pred == pred for h in r.head):
                todo += [b.pred for b in r.body]
    return False


class Match:
    """The FROM and WHERE of a conjunction of atoms over fact rows, with the column for each variable.

    Positive atoms match facts of the given polarity. A negative body atom is negation as failure: no
    positive fact matches it, with its local variables free."""

    def __init__(self, body: tuple[Atom, ...], ctx: str, guard: int | None, delta: int | None, polarity: bool = True) -> None:
        self.first: dict[Var, tuple[int, int]] = {}
        froms, conds, params = [], [], []
        positives = [(i, a) for i, a in enumerate(body) if a.positive]
        for i, atom in positives:
            froms.append(f"fact AS f{i}")
            conds += [f"f{i}.pred = ?", f"f{i}.positive = ?", f"f{i}.ctx IN ('world', ?)"]
            params += [atom.pred, int(polarity), ctx]
            for k in range(3):
                col = f"f{i}.a{k}"
                if k >= len(atom.args):
                    conds.append(f"{col} = ''")
                    continue
                t = atom.args[k]
                if isinstance(t, Const):
                    conds.append(f"{col} = ?")
                    params.append(t.id)
                    continue
                if guard is not None:
                    # A rule never reuses a skolem term it made itself, which keeps recursion finite.
                    conds.append(f"{col} NOT GLOB ?")
                    params.append(f"sk:{guard}:*")
                if t in self.first:
                    conds.append(f"{col} = {self.column(t)}")
                else:
                    self.first[t] = (i, k)
        if delta is not None and positives:
            conds.append("(" + " OR ".join(f"f{i}.round = ?" for i, _ in positives) + ")")
            params += [delta] * len(positives)
        for i, atom in enumerate(body):
            if not atom.positive:
                conds.append(self._absent(i, atom, ctx, params))
        self.n = len(positives)
        self.ids_list = [f"f{i}.id" for i, _ in positives]
        self.src = f"FROM {', '.join(froms)} WHERE {' AND '.join(conds)}" if froms else "FROM (SELECT 1) WHERE 1"
        self.params = tuple(params)

    def _absent(self, i: int, atom: Atom, ctx: str, params: list) -> str:
        local: dict[Var, str] = {}
        conds = [f"n{i}.pred = ?", "n{0}.positive = 1".format(i), f"n{i}.ctx IN ('world', ?)"]
        params += [atom.pred, ctx]
        for k in range(3):
            col = f"n{i}.a{k}"
            if k >= len(atom.args):
                conds.append(f"{col} = ''")
                continue
            t = atom.args[k]
            if isinstance(t, Const):
                conds.append(f"{col} = ?")
                params.append(t.id)
            elif t in self.first:
                conds.append(f"{col} = {self.column(t)}")
            elif t in local:
                conds.append(f"{col} = {local[t]}")
            else:
                local[t] = col
        return f"NOT EXISTS (SELECT 1 FROM fact AS n{i} WHERE {' AND '.join(conds)})"

    def column(self, v: Var) -> str:
        i, k = self.first[v]
        return f"f{i}.a{k}"

    def ids(self) -> str:
        return ", ".join(self.ids_list)


def rule_sql(rule: lf.Rule, rule_id: int, ctx: str, delta: int | None, rnd: int) -> list[Statement]:
    """Statements for one rule in one round. delta limits matches to facts from that round, once the rule has run."""
    if not rule.body:
        raise ValueError("a rule needs a body")
    m = Match(rule.body, ctx, rule_id, delta)
    bindings = " || ',' || ".join(m.column(v) for v in m.first) or "''"

    def skolem(v: Var) -> tuple[str, tuple]:
        return f"('sk:' || ? || ':' || ? || ':' || {bindings})", (rule_id, v.key)

    def term(t) -> tuple[str, tuple]:
        if isinstance(t, Const):
            return "?", (t.id,)
        if t in m.first:
            return m.column(t), ()
        return skolem(t)

    statements: list[Statement] = []
    for v in rule.creates:
        expr, p = skolem(v)
        statements.append((f"INSERT OR IGNORE INTO entity(id, kind) SELECT {expr}, 'skolem' {m.src}", (*p, *m.params)))

    for head in rule.head:
        exprs = [term(t) for t in head.args] + [("''", ())] * (3 - len(head.args))
        vals = ", ".join(e for e, _ in exprs)
        val_params = tuple(p for _, ps in exprs for p in ps)
        fact_match = " AND ".join(f"a{k} = {e}" for k, (e, _) in enumerate(exprs))
        polarity = int(head.positive)
        statements.append((
            f"INSERT OR IGNORE INTO fact(pred, a0, a1, a2, positive, ctx, round) "
            f"SELECT ?, {vals}, ?, ?, ? {m.src}",
            (head.pred, *val_params, polarity, ctx, rnd, *m.params),
        ))
        statements.append((
            "INSERT OR IGNORE INTO why(fact, sentence, rule, premises) "
            f"SELECT (SELECT id FROM fact WHERE pred = ? AND {fact_match} AND positive = ? AND ctx = ?), "
            f"NULL, ?, json_array({m.ids()}) {m.src}",
            (head.pred, *val_params, polarity, ctx, rule_id, *m.params),
        ))
    return statements

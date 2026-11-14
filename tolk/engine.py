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
            return total
        total += added
        prev = rnd


class Match:
    """The FROM and WHERE of a conjunction of atoms over fact rows, with the column for each variable."""

    def __init__(self, body: tuple[Atom, ...], ctx: str, guard: int | None, delta: int | None) -> None:
        self.first: dict[Var, tuple[int, int]] = {}
        froms, conds, params = [], [], []
        for i, atom in enumerate(body):
            froms.append(f"fact AS f{i}")
            conds += [f"f{i}.pred = ?", f"f{i}.positive = 1", f"f{i}.ctx IN ('world', ?)"]
            params += [atom.pred, ctx]
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
                self.first.setdefault(t, (i, k))
                if guard is not None:
                    # A rule never reuses a skolem term it made itself, which keeps recursion finite.
                    conds.append(f"{col} NOT GLOB ?")
                    params.append(f"sk:{guard}:*")
                if self.first[t] != (i, k):
                    conds.append(f"{col} = {self.column(t)}")
        if delta is not None:
            conds.append("(" + " OR ".join(f"f{i}.round = ?" for i in range(len(body))) + ")")
            params += [delta] * len(body)
        self.n = len(body)
        self.src = f"FROM {', '.join(froms)} WHERE {' AND '.join(conds)}"
        self.params = tuple(params)

    def column(self, v: Var) -> str:
        i, k = self.first[v]
        return f"f{i}.a{k}"

    def ids(self) -> str:
        return ", ".join(f"f{i}.id" for i in range(self.n))


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
        statements.append((
            f"INSERT OR IGNORE INTO fact(pred, a0, a1, a2, positive, ctx, round) "
            f"SELECT ?, {vals}, 1, ?, ? {m.src}",
            (head.pred, *val_params, ctx, rnd, *m.params),
        ))
        statements.append((
            "INSERT OR IGNORE INTO why(fact, sentence, rule, premises) "
            f"SELECT (SELECT id FROM fact WHERE pred = ? AND {fact_match} AND positive = 1 AND ctx = ?), "
            f"NULL, ?, json_array({m.ids()}) {m.src}",
            (head.pred, *val_params, ctx, rule_id, *m.params),
        ))
    return statements

"""Rules to SQL, run to fixpoint. Identifiers are fixed column names and generated aliases; every value is a bound parameter."""

import sqlite3

from tolk import lf, negation, store
from tolk.lf import Atom, Const, Var

Statement = tuple[str, tuple]


def run(db: sqlite3.Connection, ctx: str = "world", kinds: tuple[str, ...] = ("strict",)) -> int:
    """Run the rules of the given kinds stratum by stratum, each to fixpoint. Returns the number of facts added."""
    marks = ", ".join("?" * len(kinds))
    rules = [(rid, lf.decode_rule(text), ran) for rid, text, ran in
             db.execute(f"SELECT id, lf, ran FROM rule WHERE kind IN ({marks}) ORDER BY id", kinds)]
    level = negation.strata([r for _, r, _ in rules])
    total = 0
    rnd = store.current_round(db)
    for stratum in sorted(set(level)):
        members = [(rid, rule) for (rid, rule, _), lv in zip(rules, level) if lv == stratum]
        while True:
            rnd += 1
            before = db.execute("SELECT COUNT(*) FROM fact").fetchone()[0]
            _year_order(db, ctx, rnd)
            for rid, rule in members:
                ran = db.execute("SELECT ran FROM rule WHERE id = ?", (rid,)).fetchone()[0]
                # Facts added later in the round the rule last ran in count as new too.
                for sql, params in rule_sql(rule, rid, ctx, ran, rnd):
                    db.execute(sql, params)
                db.execute("UPDATE rule SET ran = ? WHERE id = ?", (rnd, rid))
            added = db.execute("SELECT COUNT(*) FROM fact").fetchone()[0] - before
            total += added
            if added == 0:
                break
    record_conflicts(db)
    return total


def _year_order(db: sqlite3.Connection, ctx: str, rnd: int) -> None:
    """The built-in axiom that an event in an earlier year is before an event in a later one. A year is a number, which a rule cannot compare."""
    row = db.execute("SELECT id FROM rule WHERE kind = 'axiom'").fetchone()
    if row is None:
        return
    pairs = (f"FROM fact f JOIN fact g ON f.pred = ? AND g.pred = ? AND f.positive = 1 AND g.positive = 1 "
             "AND f.a1 GLOB '[0-9]*' AND g.a1 GLOB '[0-9]*' AND CAST(f.a1 AS INTEGER) < CAST(g.a1 AS INTEGER) "
             "AND f.ctx IN ('world', ?) AND g.ctx IN ('world', ?)")
    marks = ("_in_p_temp", "_in_p_temp", ctx, ctx)
    db.execute(f"INSERT OR IGNORE INTO fact(pred, a0, a1, a2, positive, ctx, round, level) "
               f"SELECT '{lf.BEFORE}', f.a0, g.a0, '', 1, ?, ?, MAX(2, f.level, g.level) {pairs}", (ctx, rnd, *marks))
    db.execute(f"INSERT OR IGNORE INTO why(fact, sentence, rule, premises, bindings) "
               f"SELECT (SELECT id FROM fact WHERE pred = '{lf.BEFORE}' AND a0 = f.a0 AND a1 = g.a0 AND a2 = '' AND positive = 1 AND ctx = ?), "
               f"NULL, ?, json_array(f.id, g.id), f.a1 || ',' || g.a1 {pairs}", (ctx, row[0], *marks))


# A positive fact p and a negative fact n clash when they differ only in sign. A negative fact has no event, so its empty one matches any.
CLASH = (
    "FROM fact p JOIN fact n ON n.pred = p.pred AND n.ctx = p.ctx AND n.a1 = p.a1 AND n.a2 = p.a2 AND (n.a0 = p.a0 OR n.a0 = '') "
    "WHERE p.positive = 1 AND n.positive = 0"
)


def record_conflicts(db: sqlite3.Connection) -> None:
    """A positive and a negative fact that clash get a conflict row, once one of them was derived."""
    db.execute(
        "INSERT INTO conflict(positive_fact, negative_fact) "
        f"SELECT p.id, n.id {CLASH} "
        "AND (EXISTS (SELECT 1 FROM why w WHERE w.fact = p.id AND w.rule IS NOT NULL) "
        "     OR EXISTS (SELECT 1 FROM why w WHERE w.fact = n.id AND w.rule IS NOT NULL)) "
        "AND NOT EXISTS (SELECT 1 FROM conflict c WHERE c.positive_fact = p.id AND c.negative_fact = n.id)"
    )


def _pred_op(pred: str) -> str:
    """A predicate with a star names a family of predicates, such as any locative preposition."""
    return "GLOB" if "*" in pred else "="


class Match:
    """The FROM and WHERE of a conjunction of atoms over fact rows, with the column for each variable.

    Positive atoms match facts of the given polarity. A negative body atom is negation as failure: no
    positive fact matches it, with its local variables free."""

    def __init__(self, body: tuple[Atom, ...], ctx: str, guard: int | None, delta: int | None,
                 polarity: bool | tuple[int, ...] = True) -> None:
        # One polarity for every atom, or one per atom in order: which kind of stored fact each positive atom matches.
        pol = polarity if isinstance(polarity, tuple) else (int(polarity),) * len(body)
        self.first: dict[Var, tuple[int, int]] = {}
        froms, conds, params = [], [], []
        positives = [(i, a) for i, a in enumerate(body) if a.positive]
        for i, atom in positives:
            froms.append(f"fact AS f{i}")
            conds += [f"f{i}.pred {_pred_op(atom.pred)} ?", f"f{i}.positive = ?", f"f{i}.ctx IN ('world', ?)"]
            params += [atom.pred, pol[i], ctx]
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
            conds.append("(" + " OR ".join(f"f{i}.round >= ?" for i, _ in positives) + ")")
            params += [delta] * len(positives)
        for i, atom in enumerate(body):
            if not atom.positive:
                conds.append(self._absent(i, atom, ctx, params))
        self.ids_list = [f"f{i}.id" for i, _ in positives]
        self.src = f"FROM {', '.join(froms) or '(SELECT 1)'} WHERE {' AND '.join(conds) or '1'}"
        self.params = tuple(params)

    def _absent(self, i: int, atom: Atom, ctx: str, params: list) -> str:
        local: dict[Var, str] = {}
        conds = [f"n{i}.pred {_pred_op(atom.pred)} ?", f"n{i}.positive = 1", f"n{i}.ctx IN ('world', ?)"]
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
    """Statements for one rule in one round. delta limits matches to facts from that round on, once the rule has run."""
    if not rule.body:
        raise ValueError("a rule needs a body")
    m = Match(rule.body, ctx, rule_id, delta)
    bindings = " || ',' || ".join(m.column(v) for v in m.first) or "''"
    if rule.kind == "default":
        # A default instance that was defeated is not used again; the bindings name the instance.
        m.src += f" AND NOT EXISTS (SELECT 1 FROM defeat d WHERE d.rule = ? AND d.bindings = {bindings})"
        m.params += (rule_id,)
    # A fact is as strong as its weakest premise, and a default makes it the weakest kind.
    levels = ", ".join(f"{i[:-3]}.level" for i in m.ids_list)
    level = "3" if rule.kind == "default" else f"MAX(2, {levels})" if levels else "2"

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
            f"INSERT OR IGNORE INTO fact(pred, a0, a1, a2, positive, ctx, round, level) "
            f"SELECT ?, {vals}, ?, ?, ?, {level} {m.src}",
            (head.pred, *val_params, polarity, ctx, rnd, *m.params),
        ))
        statements.append((
            "INSERT OR IGNORE INTO why(fact, sentence, rule, premises, bindings) "
            f"SELECT (SELECT id FROM fact WHERE pred = ? AND {fact_match} AND positive = ? AND ctx = ?), "
            f"NULL, ?, json_array({m.ids()}), {bindings} {m.src}",
            (head.pred, *val_params, polarity, ctx, rule_id, *m.params),
        ))
    return statements

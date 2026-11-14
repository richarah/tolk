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


def rule_sql(rule: lf.Rule, rule_id: int, ctx: str, delta: int | None, rnd: int) -> list[Statement]:
    """Statements for one rule in one round. delta limits matches to facts from that round, once the rule has run."""
    if not rule.body:
        raise ValueError("a rule needs a body")
    first: dict[Var, tuple[int, int]] = {}
    for i, atom in enumerate(rule.body):
        for k, t in enumerate(atom.args):
            if isinstance(t, Var):
                first.setdefault(t, (i, k))

    def column(v: Var) -> str:
        i, k = first[v]
        return f"f{i}.a{k}"

    froms, conds, params = [], [], []
    for i, atom in enumerate(rule.body):
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
            # A binding that a rule made from its own skolem terms is never reused, which keeps recursion finite.
            conds.append(f"{col} NOT LIKE ?")
            params.append(f"sk:{rule_id}:%")
            if first[t] != (i, k):
                conds.append(f"{col} = {column(t)}")
    if delta is not None:
        conds.append("(" + " OR ".join(f"f{i}.round = ?" for i in range(len(rule.body))) + ")")
        params += [delta] * len(rule.body)
    src = f"FROM {', '.join(froms)} WHERE {' AND '.join(conds)}"
    src_params = tuple(params)

    bindings = " || ',' || ".join(column(v) for v in first) or "''"

    def skolem(v: Var) -> tuple[str, tuple]:
        return f"('sk:' || ? || ':' || ? || ':' || {bindings})", (rule_id, v.key)

    def term(t) -> tuple[str, tuple]:
        if isinstance(t, Const):
            return "?", (t.id,)
        if t in first:
            return column(t), ()
        return skolem(t)

    statements: list[Statement] = []
    for v in rule.creates:
        expr, p = skolem(v)
        statements.append((f"INSERT OR IGNORE INTO entity(id, kind) SELECT {expr}, 'skolem' {src}", (*p, *src_params)))

    for head in rule.head:
        exprs = [term(t) for t in head.args] + [("''", ())] * (3 - len(head.args))
        vals = ", ".join(e for e, _ in exprs)
        val_params = tuple(p for _, ps in exprs for p in ps)
        fact_match = " AND ".join(f"a{k} = {e}" for k, (e, _) in enumerate(exprs))
        fact_match_params = tuple(p for _, ps in exprs for p in ps)
        statements.append((
            f"INSERT OR IGNORE INTO fact(pred, a0, a1, a2, positive, ctx, round) "
            f"SELECT ?, {vals}, 1, ?, ? {src}",
            (head.pred, *val_params, ctx, rnd, *src_params),
        ))
        premises = ", ".join(f"f{i}.id" for i in range(len(rule.body)))
        statements.append((
            "INSERT OR IGNORE INTO why(fact, sentence, rule, premises) "
            f"SELECT (SELECT id FROM fact WHERE pred = ? AND {fact_match} AND positive = 1 AND ctx = ?), "
            f"NULL, ?, json_array({premises}) {src}",
            (head.pred, *fact_match_params, ctx, rule_id, *src_params),
        ))
    return statements

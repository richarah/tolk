"""A sentence that tells two things at once ("Kim sings and Sandy dances.") is two statements. Atoms that share an event or an
anonymous thing are one statement; a name does not join them, since it is the same thing in both."""

from tolk import lf


def split(x: lf.Tell) -> list[lf.Tell]:
    """The statements of a Tell, in the order their first atoms stand. Claims and notes stay with the first."""
    if x.claims:
        return [x]
    groups: list[tuple[set[str], list[lf.Atom]]] = []
    for a in x.atoms:
        joins = {t.id if isinstance(t, lf.Const) else t.key for t in a.args if _joins(t)}
        hit = [g for g in groups if g[0] & joins]
        merged = (set(joins).union(*[g[0] for g in hit]), [b for g in hit for b in g[1]] + [a])
        groups = [g for g in groups if g not in hit] + [merged]
    if len(groups) < 2:
        return [x]
    order = {id(a): n for n, a in enumerate(x.atoms)}
    groups.sort(key=lambda g: min(order[id(a)] for a in g[1]))
    return [lf.Tell(tuple(sorted(atoms, key=lambda a: order[id(a)])), x.mentions if n == 0 else (), x.notes if n == 0 else ()) for n, (_, atoms) in enumerate(groups)]


def _joins(t) -> bool:
    return not (isinstance(t, lf.Const) and t.kind == "named")


def each(mind, text: str, parts: list[lf.Tell], head: tuple, trust: int, observation: bool, result):
    """Store each statement with a sentence of its own, all or none. The reply is the sentence's: how many facts were new."""
    mind.db.execute("SAVEPOINT statements")
    outcomes = []
    for part in parts:
        got = mind._store(text, part, (head[0], head[1], lf.show(part)), trust, observation)
        if not got.outcome.startswith(("stored", "already told")):
            mind.db.execute("ROLLBACK TO statements")
            mind.db.execute("RELEASE statements")
            return result(*head, outcome=got.outcome)
        outcomes.append(got.outcome)
    mind.db.execute("RELEASE statements")
    new = sum(int(o.split()[1]) for o in outcomes if o.startswith("stored"))
    return result(*head, outcome=f"stored, {new} new fact(s)" if new else outcomes[0])

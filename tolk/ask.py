"""Questions: an answer from the positive facts that match, with the proof of each matched fact."""

import json
from dataclasses import dataclass

from tolk import engine, lf

YES, NO, UNKNOWN, CONFLICT = "Yes", "No", "Unknown", "Conflict"


@dataclass(frozen=True)
class Proof:
    fact: int
    sentence: int | None
    rule: int | None
    premises: tuple["Proof", ...]


@dataclass(frozen=True)
class Answer:
    value: str
    solutions: tuple[tuple[str, ...], ...]  # the wanted variables' constants, one tuple per solution
    proofs: tuple[tuple[Proof, ...], ...]  # for each solution, one proof per body atom


def answer(db, q: lf.Ask, ctx: str = "world") -> Answer:
    m = engine.Match(q.body, ctx, None, None)
    wanted = [m.column(v) for v in q.wanted]
    select = ", ".join(wanted + [m.ids()])
    rows = db.execute(f"SELECT {select} {m.src} ORDER BY f0.id", m.params).fetchall()
    n = len(wanted)
    seen: dict[tuple[str, ...], tuple[Proof, ...]] = {}
    for row in rows:
        values = tuple(row[:n])
        if values not in seen:
            seen[values] = tuple(prove(db, fid) for fid in row[n:])
    if not seen:
        return Answer(UNKNOWN, (), ())
    if not q.wanted:
        return Answer(YES, (), (seen[()],))
    solutions = sorted(seen)
    return Answer(YES, tuple(solutions), tuple(seen[s] for s in solutions))


def prove(db, fact_id: int) -> Proof:
    sentence, rule, premises = db.execute(
        "SELECT sentence, rule, premises FROM why WHERE fact = ? ORDER BY rowid LIMIT 1", (fact_id,)
    ).fetchone()
    return Proof(fact_id, sentence, rule, tuple(prove(db, p) for p in json.loads(premises)))

"""Questions: an answer from the positive facts that match, with the proof of each matched fact."""

import json
import sqlite3
from dataclasses import dataclass

from tolk import engine, lf

YES, NO, UNKNOWN, CONFLICT = "Yes", "No", "Unknown", "Conflict"
# For Conflict, proofs holds the positive proof set, then the negative one.


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


def answer(db: sqlite3.Connection, q: lf.Ask, ctx: str = "world") -> Answer:
    pos = _solutions(db, q, True, ctx)
    if not q.wanted:
        neg = _solutions(db, q, False, ctx)
        if pos and neg:
            return Answer(CONFLICT, (), (pos[()], neg[()]))
        if pos:
            return Answer(YES, (), (pos[()],))
        if neg:
            return Answer(NO, (), (neg[()],))
        return Answer(UNKNOWN, (), ())
    if not pos:
        return Answer(UNKNOWN, (), ())
    solutions = sorted(pos)
    return Answer(YES, tuple(solutions), tuple(pos[s] for s in solutions))


def _solutions(db: sqlite3.Connection, q: lf.Ask, polarity: bool, ctx: str) -> dict[tuple[str, ...], tuple[Proof, ...]]:
    """For each distinct value of the wanted variables, one proof per positive body atom of the first matching row."""
    m = engine.Match(q.body, ctx, None, None, polarity)
    wanted = [m.column(v) for v in q.wanted]
    rows = db.execute(f"SELECT {', '.join(wanted + [m.ids()])} {m.src} ORDER BY {m.ids()}", m.params).fetchall()
    n = len(wanted)
    seen: dict[tuple[str, ...], tuple[Proof, ...]] = {}
    for row in rows:
        values = tuple(row[:n])
        if values not in seen:
            seen[values] = tuple(prove(db, fid) for fid in row[n:])
    return seen


def prove(db: sqlite3.Connection, fact_id: int) -> Proof:
    sentence, rule, premises = db.execute(
        "SELECT sentence, rule, premises FROM why WHERE fact = ? ORDER BY rowid LIMIT 1", (fact_id,)
    ).fetchone()
    return Proof(fact_id, sentence, rule, tuple(prove(db, p) for p in json.loads(premises)))

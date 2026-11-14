"""Questions: an answer from the positive facts that match, with the proof of each matched fact."""

import json
import re
import sqlite3
from dataclasses import dataclass

from tolk import engine, lf
from tolk.lf import Atom

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
    widened: tuple[str, ...] = ()  # "asked matched as stored" for each preposition sense that was widened


PREPOSITION = re.compile(r"_([^_]+)_p_[^_]+")


def answer(db: sqlite3.Connection, q: lf.Ask, ctx: str = "world") -> Answer:
    """Answer exactly; only if that finds nothing, let a preposition match a stored sense of the same lemma."""
    exact = _answer(db, q, ctx)
    if exact.value != UNKNOWN or not any(PREPOSITION.fullmatch(a.pred) for a in q.body):
        return exact
    wide = lf.Ask(tuple(
        Atom(f"_{m.group(1)}_p_*", a.args, a.positive) if (m := PREPOSITION.fullmatch(a.pred)) else a for a in q.body
    ), q.wanted)
    got = _answer(db, wide, ctx)
    if got.value == UNKNOWN:
        return exact
    asked = [a.pred for a in q.body if PREPOSITION.fullmatch(a.pred)]
    stored = {db.execute("SELECT pred FROM fact WHERE id = ?", (p.fact,)).fetchone()[0] for sol in got.proofs for p in sol}
    notes = tuple(f"{a} matched as {b}" for a in asked for b in sorted(stored)
                  if b != a and b.startswith(a.rsplit("_", 1)[0] + "_"))
    return Answer(got.value, got.solutions, got.proofs, notes)


def _answer(db: sqlite3.Connection, q: lf.Ask, ctx: str) -> Answer:
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

"""Questions: an answer from the positive facts that match, with the proof of each matched fact."""

import dataclasses
import json
import re
import sqlite3
from dataclasses import dataclass

from tolk import engine, lf
from tolk.lf import Atom, Var

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
    count: int | None = None  # for how many: the number of distinct things found
    by_default: bool = False  # for a question about every thing: it holds, or fails, only through a default


PREPOSITION = re.compile(r"_([^_]+)_p_[^_]+")


def answer(db: sqlite3.Connection, q: lf.Ask, ctx: str = "world") -> Answer:
    if q.alternatives:
        return _any(q, [_widening(db, dataclasses.replace(q, body=alt, alternatives=()), ctx) for alt in q.alternatives])
    return _widening(db, q, ctx)


def _any(q: lf.Ask, parts: list[Answer]) -> Answer:
    """An or: Yes if either side is, with that side's proof. Otherwise No if every side is No, else Unknown."""
    yes = [p for p in parts if p.value == YES]
    if yes:
        if q.wanted:
            solutions = tuple(sorted({s for p in yes for s in p.solutions}))
            return Answer(YES, solutions, tuple(pr for p in yes for pr in p.proofs), tuple(w for p in yes for w in p.widened))
        return yes[0]
    if all(p.value == NO for p in parts):
        return parts[0]
    return Answer(UNKNOWN, (), ())


def _widening(db: sqlite3.Connection, q: lf.Ask, ctx: str) -> Answer:
    """Answer exactly; only if that finds nothing, let a preposition match a stored sense of the same lemma, and a word the grammar
    did not recognise match the same word under its other guessed part of speech (noun for adjective, adjective for noun)."""
    exact = _answer(db, q, ctx)
    wide_atoms = tuple(_widen(a) for a in q.body)
    if exact.value != UNKNOWN or wide_atoms == q.body:
        return exact
    got = _answer(db, dataclasses.replace(q, body=wide_atoms), ctx)
    if got.value == UNKNOWN:
        return exact
    asked = [a.pred for a, w in zip(q.body, wide_atoms) if a != w]
    stored = {db.execute("SELECT pred FROM fact WHERE id = ?", (p.fact,)).fetchone()[0] for sol in got.proofs for p in sol}
    notes = tuple(f"{a} matched as {b}" for a in asked for b in sorted(stored) if b != a and _same_word(a, b))
    return Answer(got.value, got.solutions, got.proofs, notes, got.count)


def _same_word(asked: str, stored: str) -> bool:
    a, b = PREPOSITION.fullmatch(asked), PREPOSITION.fullmatch(stored)
    if a and b:
        return a.group(1) == b.group(1)
    a, b = lf.UNKNOWN_PRED.fullmatch(asked), lf.UNKNOWN_PRED.fullmatch(stored)
    return bool(a and b and a.group(1) == b.group(1))


def _widen(a: Atom) -> Atom:
    if m := PREPOSITION.fullmatch(a.pred):
        return Atom(f"_{m.group(1)}_p_*", a.args, a.positive)
    if m := lf.UNKNOWN_PRED.fullmatch(a.pred):
        # An adjective takes an event, a noun does not, so the other part of speech has the other shape.
        if m.group(2) == "n":
            return Atom(f"_{m.group(1)}_a_{lf.UNKNOWN_SENSE}", (Var("ewiden"), *a.args), a.positive)
        if m.group(2) == "a":
            return Atom(f"_{m.group(1)}_n_{lf.UNKNOWN_SENSE}", a.args[1:], a.positive)
    return a


def _answer(db: sqlite3.Connection, q: lf.Ask, ctx: str) -> Answer:
    """What the question claims is matched against facts of the polarity it states; the opposite against the other kind.
    A negated question claims negative facts, and its opposite is the positive ones, so Yes and No swap."""
    claim, against = _polarities(q)
    if q.count is not None:
        return _counted(db, q, claim, ctx)
    pos = _solutions(db, q, claim, ctx)
    if not q.wanted:
        neg = _solutions(db, q, against, ctx)
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


def _counted(db: sqlite3.Connection, q: lf.Ask, claim: tuple[int, ...], ctx: str) -> Answer:
    """How many distinct things the known facts give; or, with atleast, whether there are at least that many."""
    found = _solutions(db, lf.Ask(q.body, (q.count,)), claim, ctx)
    n = len(found)
    solutions = sorted(found)
    proofs = tuple(found[v] for v in solutions)
    if not q.atleast:
        return Answer(YES, tuple(solutions), proofs, count=n)
    if n >= q.atleast:
        return Answer(YES, (), (tuple(p for ps in proofs[: q.atleast] for p in ps),))
    return Answer(UNKNOWN, (), ())


def _polarities(q: lf.Ask) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Per atom, the kind of fact that supports the question and the kind that opposes it."""
    claim = tuple(int(a.positive) for a in q.body)
    if any(a.pred == lf.BEFORE for a in q.body):
        # The opposite of "A before B" is the reverse order, which is known if B is known to be before A; the events themselves are not negated.
        return claim, tuple(0 if a.pred == lf.BEFORE else 1 for a in q.body)
    if all(claim):
        return claim, (0,) * len(claim)
    return claim, (1,) * len(claim)


def _solutions(db: sqlite3.Connection, q: lf.Ask, polarity: tuple[int, ...], ctx: str) -> dict[tuple[str, ...], tuple[Proof, ...]]:
    """For each distinct value of the wanted variables, one proof per body atom of the first matching row."""
    flat = tuple(Atom(a.pred, a.args) for a in q.body)
    m = engine.Match(flat, ctx, None, None, polarity)
    src, params = m.src, m.params
    for var, tense in q.tenses:
        if var in m.first:
            # A fact about an event matches a past question only if the event is past, and a present one only if it is not.
            # A fact with no event is tenseless and matches either.
            col = m.column(var)
            past = f"EXISTS (SELECT 1 FROM fact t WHERE t.pred = '{lf.TENSE}' AND t.a0 = {col} AND t.a1 = 'past' AND t.ctx IN ('world', ?))"
            src += f" AND ({col} = '' OR {'' if tense == 'past' else 'NOT '}{past})"
            params += (ctx,)
    wanted = [m.column(v) for v in q.wanted]
    rows = db.execute(f"SELECT {', '.join(wanted + [m.ids()])} {src} ORDER BY {m.ids()}", params).fetchall()
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

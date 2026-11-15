"""Why a conflict holds and what could end it: the sentences in its two proofs, weakest first."""

import sqlite3
from dataclasses import dataclass

from tolk import say
from tolk.ask import prove

KIND_ORDER = {"default": 0, "strict": 1, "told": 2}


@dataclass(frozen=True)
class Candidate:
    sentence: int
    text: str
    kind: str  # default, strict or told: what the sentence contributed
    trust: int


@dataclass(frozen=True)
class Diagnosis:
    conflict: tuple[str, str]  # the two clashing facts, worded
    candidates: tuple[Candidate, ...]  # weakest first


def diagnose(db: sqlite3.Connection) -> list[Diagnosis]:
    """For each conflict, the sentences whose removal would end it, weakest first: defaults, then strict rules, then told facts,
    then lower trust, then the more recent. An observation is never a candidate."""
    out = []
    for pos, neg in db.execute("SELECT positive_fact, negative_fact FROM conflict").fetchall():
        found: dict[int, Candidate] = {}
        for fid in (pos, neg):
            _sources(db, prove(db, fid), found)
        ordered = sorted(found.values(), key=lambda c: (KIND_ORDER[c.kind], c.trust, -c.sentence))
        out.append(Diagnosis((say.fact_text(db, pos), say.fact_text(db, neg)), tuple(ordered)))
    return out


def _sources(db: sqlite3.Connection, p, found: dict[int, Candidate]) -> None:
    if p.sentence is not None:
        _candidate(db, found, p.sentence, "told")
    if p.rule is not None:
        sentence, kind = db.execute("SELECT sentence, kind FROM rule WHERE id = ?", (p.rule,)).fetchone()
        _candidate(db, found, sentence, kind)
    for q in p.premises:
        _sources(db, q, found)


def _candidate(db: sqlite3.Connection, found: dict[int, Candidate], sentence: int, kind: str) -> None:
    text, trust, observation = db.execute("SELECT text, trust, observation FROM sentence WHERE id = ?", (sentence,)).fetchone()
    if not observation and sentence not in found:
        found[sentence] = Candidate(sentence, text, kind, trust)


def report(db: sqlite3.Connection, fresh: set[tuple[str, str]]) -> str:
    lines = []
    for d in diagnose(db):
        if d.conflict in fresh:
            lines.append(f"conflict: {d.conflict[0]} against {d.conflict[1]}; could be ended by removing: "
                         + "; ".join(f'"{c.text}" ({c.kind})' for c in d.candidates))
    return "\n".join(lines)

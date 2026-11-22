"""Wording a fact through the grammar. A skeleton (tolk/skeletons.json, made by scripts/skeletons.py from recorded fixtures) is filled with
the fact's predicate and names and given to the parser's generator. A generated sentence is kept only if parsing and compiling it gives
back exactly the fact. Of those kept the shortest wins, and the first alphabetically among equals. Otherwise the template in say.py is used,
and the wording says so."""

import json
import re
import sqlite3
from pathlib import Path
from typing import NamedTuple

from tolk import compile as comp, erg, lf, say, sem, store
from tolk.lf import Atom, Const
from tolk.rules import claims

SKELETONS = json.loads((Path(__file__).parent / "skeletons.json").read_text())
CLASS = re.compile(r"_[^_]+_([nav])_.*")
NAME = re.compile(r"[a-z]+")


class Wording(NamedTuple):
    text: str
    how: str  # generated, or template: the fallback, marked for debug output


def pattern(pred: str, entities: int, positive: bool) -> str:
    """Which skeleton a fact takes: by the class of its predicate, how many things it is about, and its polarity."""
    kind = {"n": "noun", "a": "adj"}.get((m := CLASS.fullmatch(pred)) and m.group(1), f"verb{entities}")
    return kind if positive else f"not_{kind}"


def word(db: sqlite3.Connection, fact_id: int) -> Wording:
    pred, a0, a1, a2, positive = db.execute("SELECT pred, a0, a1, a2, positive FROM fact WHERE id = ?", (fact_id,)).fetchone()
    shape = CLASS.fullmatch(pred)
    things = [a for a in ((a0,) if shape and shape.group(1) == "n" else (a1, a2)) if a]
    if shape and all(NAME.fullmatch(t) and t not in say.SPEAKERS and _named(db, t) for t in things):
        found = pick(_accepted(db, fact_id, pred, things, bool(positive)))
        if found:
            return Wording(found, "generated")
    return Wording(say.fact_text(db, fact_id), "template")


def pick(sentences: set[str]) -> str | None:
    """The shortest sentence, and the first alphabetically among equals."""
    return min(sentences, key=lambda s: (len(s), s), default=None)


def _named(db: sqlite3.Connection, thing: str) -> bool:
    return db.execute("SELECT 1 FROM entity WHERE id = ? AND kind = 'named'", (thing,)).fetchone() is not None


def _accepted(db: sqlite3.Connection, fact_id: int, pred: str, things: list[str], positive: bool) -> set[str]:
    known = store.known_preds(db)
    out: set[str] = set()
    for template in SKELETONS.get(pattern(pred, len(things), positive), []):
        mrs = template.replace("{p}", pred)
        for slot, thing in zip("ab", things):
            mrs = mrs.replace("{" + slot + "}", thing.title())
        out |= {s for s in erg.generate(mrs) if _gives_back(s, pred, things, positive, known)}
    return out


def _gives_back(sentence: str, pred: str, things: list[str], positive: bool, known: set) -> bool:
    readings = [sem.read(p.mrs, p.lex) for p in erg.parse(sentence)]
    _, x = comp.choose(readings, known)
    if not isinstance(x, lf.Tell):
        return False
    event = [] if CLASS.fullmatch(pred).group(1) == "n" else [Const("", lf.NO_EVENT) if not positive else Const("e1", "event")]
    fact = Atom(pred, tuple(event + [Const(t) for t in things]), positive)
    return {claims.claim_key((a,)) for a in x.atoms if a.pred not in (lf.TENSE, lf.MODAL)} == {claims.claim_key((fact,))}

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
        # A negative fact is worded with the tense, modal and progressive of its event: "Kim didn't sing.", "Kim can't sing.".
        marks = _marks(db, a0) if not positive and shape.group(1) != "n" else None
        found = pick(_accepted(db, fact_id, pred, things, bool(positive), marks))
        if found:
            return Wording(found, "generated")
    return Wording(say.fact_text(db, fact_id), "template")


def _marks(db: sqlite3.Connection, event: str) -> tuple[str, tuple[str, ...]] | None:
    """The tense (past, fut or "" for present) and the modal kinds of a stored event. None for the empty event of a derived negative
    fact, which no sentence gives back."""
    if not event:
        return None
    tense = db.execute("SELECT MIN(a1) FROM fact WHERE pred = ? AND a0 = ? AND positive = 1", (lf.TENSE, event)).fetchone()[0] or ""
    modals = tuple(sorted(k for (k,) in db.execute("SELECT DISTINCT a1 FROM fact WHERE pred = ? AND a0 = ? AND positive = 1", (lf.MODAL, event))))
    return tense, modals


def _marked(mrs: str, marks: tuple[str, tuple[str, ...]]) -> list[str]:
    """The skeleton of a negative fact with the tense and progressive of the sentence's event, or with a modal: one version with the
    negation over the modal ("can't sing") and one with the modal over the negation ("mustn't sing"). Empty if it cannot be marked."""
    tense, modals = marks
    index = "INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]"
    if index not in mrs:
        return []
    kinds = [k for k in modals if k != "prog"]
    if len(kinds) > 1 or (kinds and (tense or "prog" in modals)):
        return []
    props = f"TENSE: {tense or 'pres'} MOOD: indicative PROG: {'+' if 'prog' in modals else '-'} PERF: -"
    if not kinds:
        return [mrs.replace(index, f"INDEX: e2 [ e SF: prop {props} ]")]
    # The modal takes the sentence's event and a clause; the verb's event is untensed.
    neg = re.search(r"\[ neg LBL: (h\d+) ARG0: e\d+ \[[^\]]*\] ARG1: (h\d+) \]", mrs)
    verb = re.search(r"\[ \{p\} LBL: (h\d+) ARG0: e2 ", mrs)
    if neg is None or verb is None or f"{neg.group(2)} qeq {verb.group(1)}" not in mrs or f"h0 qeq {neg.group(1)}" not in mrs:
        return []
    modal = f"  [ _{kinds[0]}_v_modal LBL: h90 ARG0: e91 ARG1: h92 ]"
    base = mrs.replace(index, f"INDEX: e91 [ e SF: prop {props} ]")
    base = base.replace(verb.group(0), "[ {p} LBL: " + verb.group(1) + " ARG0: e2 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ")
    base = base.replace(neg.group(0), neg.group(0) + modal)
    over = base.replace(f"{neg.group(2)} qeq {verb.group(1)}", f"{neg.group(2)} qeq h90 h92 qeq {verb.group(1)}")
    under = base.replace(f"h0 qeq {neg.group(1)}", f"h0 qeq h90 h92 qeq {neg.group(1)}")
    return [over, under]


def pick(sentences: set[str]) -> str | None:
    """The shortest sentence, and the first alphabetically among equals."""
    return min(sentences, key=lambda s: (len(s), s), default=None)


def _named(db: sqlite3.Connection, thing: str) -> bool:
    return db.execute("SELECT 1 FROM entity WHERE id = ? AND kind = 'named'", (thing,)).fetchone() is not None


def _accepted(db: sqlite3.Connection, fact_id: int, pred: str, things: list[str], positive: bool,
              marks: tuple[str, tuple[str, ...]] | None = None) -> set[str]:
    """Generated sentences that give back the fact. With marks (a negative fact's event), the sentence must give back its tense and
    modals too; a negative fact with the empty event of a rule (marks None) is not given back by any sentence, which has an event."""
    known = store.known_preds(db)
    out: set[str] = set()
    if not positive and CLASS.fullmatch(pred).group(1) != "n" and marks is None:
        return out
    for template in SKELETONS.get(pattern(pred, len(things), positive), []):
        for mrs in ([template] if marks is None else _marked(template, marks)):
            mrs = mrs.replace("{p}", pred)
            for slot, thing in zip("ab", things):
                mrs = mrs.replace("{" + slot + "}", thing.title())
            out |= {s for s in erg.generate(mrs) if _gives_back(s, pred, things, positive, known, marks)}
    return out


def _gives_back(sentence: str, pred: str, things: list[str], positive: bool, known: set,
                marks: tuple[str, tuple[str, ...]] | None = None) -> bool:
    readings = [sem.read(p.mrs, p.lex) for p in erg.parse(sentence)]
    _, x = comp.choose(readings, known)
    if not isinstance(x, lf.Tell):
        return False
    event = Const("e1", "event")
    fact = Atom(pred, tuple(([] if CLASS.fullmatch(pred).group(1) == "n" else [event]) + [Const(t) for t in things]), positive)
    if marks is None:
        return {claims.claim_key((a,)) for a in x.atoms if a.pred not in (lf.TENSE, lf.MODAL)} == {claims.claim_key((fact,))}
    tense, modals = marks
    wanted = (fact,) + ((Atom(lf.TENSE, (event, Const(tense, "value"))),) if tense else ()) + tuple(
        Atom(lf.MODAL, (event, Const(k, "value"))) for k in modals)
    return claims.claim_key(x.atoms) == claims.claim_key(wanted)

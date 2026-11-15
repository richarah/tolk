"""Time in the store: the built-in axioms about order, and the events an ordering shares between sentences."""

import dataclasses
import sqlite3

from tolk import lf, store
from tolk.lf import Atom, Const, Var


def ensure_time_axioms(db: sqlite3.Connection) -> None:
    """The built-in axioms about order, stored as rules with a sentence each, so that a proof can name them.
    Made when the first ordering or year is told, so a store that never mentions time has none."""
    if db.execute("SELECT 1 FROM meta WHERE key = 'time_axioms'").fetchone():
        return
    x, y, z, e1, e2 = (Var(n) for n in ("x", "y", "z", "e1", "e2"))
    before = lambda a, b, pos=True: Atom(lf.BEFORE, (a, b), pos)
    axioms = [
        ("[axiom] before is transitive", lf.Rule((before(x, z),), (before(x, y), before(y, z))), "strict"),
        ("[axiom] before is asymmetric", lf.Rule((before(y, x, False),), (before(x, y),)), "strict"),
        ("[axiom] an event in an earlier year is before an event in a later year",
         lf.Rule((before(e1, e2),), (Atom("_in_p_temp", (e1, Var("y1"))), Atom("_in_p_temp", (e2, Var("y2"))))), "axiom"),
    ]
    for text, rule, kind in axioms:
        sid = store.add_sentence(db, text)
        db.execute("INSERT INTO rule(sentence, printed, lf, ran, kind) VALUES (?, ?, ?, NULL, ?)", (sid, text, lf.encode_rule(rule), kind))
    db.execute("INSERT INTO meta(key, value) VALUES ('time_axioms', '1')")


def reuse_events(db: sqlite3.Connection, t: lf.Tell, ctx: str) -> lf.Tell:
    """An event that an ordering mentions is the event an earlier sentence told, if that one has exactly the same content, so that
    orderings chain: in "A before B" and "B before C" the two B are one event. Other events stay fresh, as a repeated sentence adds nothing."""
    ordered = {x for a in t.atoms if a.pred == lf.BEFORE for x in a.args if isinstance(x, Const) and x.kind == "event"}
    swap: dict[Const, Const] = {}
    for e in sorted(ordered, key=lambda c: c.id):
        about = [a for a in t.atoms if a.pred != lf.BEFORE and a.args and a.args[0] == e]
        if not about or any(isinstance(x, Const) and x.kind in lf.FRESH for a in about for x in a.args[1:]):
            continue
        for (cand,) in db.execute("SELECT DISTINCT a0 FROM fact WHERE pred = ? AND ctx IN ('world', ?) AND a0 != ''", (about[0].pred, ctx)).fetchall():
            if all(_has(db, a, cand, ctx) for a in about) and Const(cand, "named") not in swap.values():
                swap[e] = Const(cand, "named")
                break
    if not swap:
        return t
    return dataclasses.replace(t, atoms=tuple(
        Atom(a.pred, tuple(swap.get(x, x) if isinstance(x, Const) else x for x in a.args), a.positive) for a in t.atoms))


def _has(db: sqlite3.Connection, a: Atom, event: str, ctx: str) -> bool:
    rest = [x.id for x in a.args[1:] if isinstance(x, Const)]
    rest += [""] * (2 - len(rest))
    return db.execute("SELECT 1 FROM fact WHERE pred = ? AND a0 = ? AND a1 = ? AND a2 = ? AND positive = ? AND ctx IN ('world', ?)",
                      (a.pred, event, rest[0], rest[1], int(a.positive), ctx)).fetchone() is not None

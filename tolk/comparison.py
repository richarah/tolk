"""Comparisons in the store: the built-in axioms for each adjective, and the answer to "Who is the tallest?"."""

import sqlite3

from tolk import lf, store
from tolk.ask import UNKNOWN, YES, Answer, prove
from tolk.lf import Atom, Var
from tolk.rules.comparatives import PREFIX


def ensure_axioms(db: sqlite3.Connection, pred: str) -> None:
    """For this adjective, comparison is transitive and asymmetric. Stored as rules with a sentence each, so that a proof can name them."""
    key = f"comparison_axioms:{pred}"
    if db.execute("SELECT 1 FROM meta WHERE key = ?", (key,)).fetchone():
        return
    x, y, z = Var("x"), Var("y"), Var("z")
    axioms = [
        (f"[axiom] {pred} is transitive", lf.Rule((Atom(pred, (x, z)),), (Atom(pred, (x, y)), Atom(pred, (y, z))))),
        (f"[axiom] {pred} is asymmetric", lf.Rule((Atom(pred, (y, x), False),), (Atom(pred, (x, y)),))),
    ]
    for text, rule in axioms:
        sid = store.add_sentence(db, text)
        db.execute("INSERT INTO rule(sentence, printed, lf, ran, kind) VALUES (?, ?, ?, NULL, 'strict')", (sid, text, lf.encode_rule(rule)))
    db.execute("INSERT INTO meta(key, value) VALUES (?, '1')", (key,))


def extreme(db: sqlite3.Connection, ctx: str, adjective: str) -> Answer:
    """The one known thing that is above every thing it is compared with, if there is exactly one. Things never compared are not known."""
    pairs = db.execute("SELECT id, a0, a1 FROM fact WHERE pred = ? AND positive = 1 AND ctx IN ('world', ?)", (PREFIX + adjective, ctx)).fetchall()
    below = {b for _, _, b in pairs}
    tops = sorted({a for _, a, _ in pairs} - below)
    if len(tops) != 1:
        return Answer(UNKNOWN, (), ())
    return Answer(YES, ((tops[0],),), (tuple(prove(db, fid) for fid, a, _ in pairs if a == tops[0]),))

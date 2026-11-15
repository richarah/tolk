"""Parse a sentence and choose its reading. The first five readings are tried; a refusal there with the parser's cap reached gets one
wider parse, chosen by the same order, and the wider result stands only if it is not a refusal."""

import sqlite3

from tolk import compile as comp, erg, lf, sem, store, words


def read(db: sqlite3.Connection, text: str, lookup, history) -> tuple[list, int, lf.LF]:
    """(readings, index of the chosen one, what it compiles to)."""
    known = store.known_preds(db)
    readings = [sem.read(p.mrs, p.lex) for p in words.parse(db, text)]
    k, x = comp.choose(readings, known, lookup, history)
    names = words.lowercase_names(text, readings[k:k + 1])
    if names or not readings or (isinstance(x, lf.Refusal) and x.code == "UNKNOWN_WORD"):
        again = [sem.read(p.mrs, p.lex) for p in words.offered(text, readings, names)]
        k2, x2 = comp.choose(again, known, lookup, history) if again else (k, x)
        if not isinstance(x2, lf.Refusal) and not words.lowercase_names(text, again[k2:k2 + 1]):
            return again, k2, x2
        if names:  # a small-letter word taken for a name is not a name: it is a word the grammar lacks
            return readings, k, lf.Refusal("UNKNOWN_WORD", sorted(names)[0])
    if isinstance(x, lf.Refusal) and len(readings) >= erg.READINGS:
        wide = [sem.read(p.mrs, p.lex) for p in words.parse(db, text, erg.WIDE)]
        k2, x2 = comp.choose(wide, known, lookup, history, after=erg.READINGS)
        if not isinstance(x2, lf.Refusal):
            return wide, k2, x2
    return readings, k, x

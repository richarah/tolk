"""Parse a sentence and choose its reading. The first five readings are tried; a refusal there with the parser's cap reached gets one
wider parse, chosen by the same order, and the wider result stands only if it is not a refusal."""

import re

from tolk import compile as comp, erg, lf, sem, words

UNDERSCORED = re.compile(r"\w*_\w*")  # the parser names such a word with an underscore its meaning structure cannot carry


def read(known: set, tags: dict, text: str, lookup=None, history=None) -> tuple[list, int, lf.LF]:
    """(readings, index of the chosen one, what it compiles to). `known` is the predicates in the store, `tags` the classes of the words
    the caller remembers."""
    if found := UNDERSCORED.search(text):
        return [], 0, lf.Refusal("UNKNOWN_WORD", found.group(0))
    readings = [sem.read(p.mrs, p.lex) for p in words.parse(tags, text)]
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
        wide = [sem.read(p.mrs, p.lex) for p in words.parse(tags, text, erg.WIDE)]
        k2, x2 = comp.choose(wide, known, lookup, history, after=erg.READINGS)
        if not isinstance(x2, lf.Refusal):
            return wide, k2, x2
    return readings, k, x

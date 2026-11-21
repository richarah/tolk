"""Parse a sentence and choose its reading. The first five readings are tried; a refusal there with the parser's cap reached gets one
wider parse, chosen by the same order, and the wider result stands only if it is not a refusal."""

import re

from tolk import compile as comp, erg, lf, sem, words

UNDERSCORED = re.compile(r"\w*_\w*")  # the parser names such a word with an underscore its meaning structure cannot carry


AUXILIARY = re.compile(r"(?P<aux>is|are|was|were|does|do|did|can|will|could|would|should|may|might)\s+(?P<first>.+?)\s+or\s+"
                       r"(?P<second>\S+\s+\S.*?)\s*\?", re.IGNORECASE)
AUXILIARIES = {"is", "are", "was", "were", "does", "do", "did", "can", "will", "could", "would", "should", "may", "might"}


def with_auxiliary(text: str) -> str | None:
    """"Is Kim happy or Lee happy?" with the auxiliary written out in the second clause, which the grammar needs to read two clauses
    ("Lee" is otherwise taken to modify "happy"). None when the text is not a question of that shape."""
    m = AUXILIARY.fullmatch(text.strip())
    if m is None or m.group("second").split()[0].lower() in AUXILIARIES:
        return None
    return f"{m.group('aux')} {m.group('first')} or {m.group('aux').lower()} {m.group('second')}?"


def _word_that_stops_it(text: str) -> str | None:
    """For a sentence the parser cannot read at all: the small-letter word whose replacement by a capitalised name makes it read, and
    compile, as a sentence. That word is the one the grammar lacks, or the one in the wrong place. None when no single replacement helps."""
    for m in re.finditer(r"\b[a-z]+\b", text):
        candidate = text[:m.start()] + "Zed" + text[m.end():]
        readings = [sem.read(p.mrs, p.lex) for p in words.parse({}, candidate)]
        if not readings:
            continue
        x = comp.choose(readings, set())[1]
        # The stand-in must be the whole of what replaces the word: a reading that takes the word into a compound name does not count.
        shown = lf.show(x)
        if not isinstance(x, lf.Refusal) and "zed" in shown.lower() and m.group(0) not in shown.lower():
            return m.group(0)
    return None


def read(known: set, tags: dict, text: str, lookup=None, history=None) -> tuple[list, int, lf.LF]:
    """(readings, index of the chosen one, what it compiles to). `known` is the predicates in the store, `tags` the classes of the words
    the caller remembers."""
    return read_as(known, tags, text, lookup, history)[1:]


def read_as(known: set, tags: dict, text: str, lookup=None, history=None) -> tuple[str, list, int, lf.LF]:
    """The same, with the text the readings are of: the question read again with its auxiliary repeated is a different string."""
    readings, k, x = read_text(known, tags, text, lookup, history)
    if isinstance(x, lf.Refusal) and (again := with_auxiliary(text)):
        readings2, k2, x2 = read_text(known, tags, again, lookup, history)
        if isinstance(x2, lf.Ask) and x2.alternatives:
            return again, readings2, k2, x2
    return text, readings, k, x


def read_text(known: set, tags: dict, text: str, lookup=None, history=None) -> tuple[list, int, lf.LF]:
    if found := UNDERSCORED.search(text):
        return [], 0, lf.Refusal("UNKNOWN_WORD", found.group(0))
    readings = [sem.read(p.mrs, p.lex) for p in words.parse(tags, text)]
    if not readings and (word := _word_that_stops_it(text)):
        return [], 0, lf.Refusal("UNKNOWN_WORD", word)
    k, x = comp.choose(readings, known, lookup, history)
    names = words.lowercase_names(text, readings[k:k + 1])
    if names or not readings or (isinstance(x, lf.Refusal) and x.code == "UNKNOWN_WORD"):
        again = [sem.read(p.mrs, p.lex) for p in words.offered(text, readings, names)]
        k2, x2 = comp.choose(again, known, lookup, history) if again else (0, lf.Refusal("NO_EVENT_READING", "the grammar gave no reading"))
        if again and not isinstance(x2, lf.Refusal) and not words.lowercase_names(text, again[k2:k2 + 1]):
            return again, k2, x2
        if names:  # a small-letter word taken for a name is not a name: it is a word the grammar lacks
            return readings, k, lf.Refusal("UNKNOWN_WORD", sorted(names)[0])
    if isinstance(x, lf.Refusal) and not lf.is_final(x) and len(readings) >= erg.READINGS:  # a final refusal is a reading understood and declined
        wide = [sem.read(p.mrs, p.lex) for p in words.parse(tags, text, erg.WIDE)]
        k2, x2 = comp.choose(wide, known, lookup, history, after=erg.READINGS)
        if not isinstance(x2, lf.Refusal):
            return wide, k2, x2
    return readings, k, x

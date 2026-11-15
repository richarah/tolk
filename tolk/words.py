"""Words the grammar does not know. The store keeps the class each was first used as, and a later sentence that uses one is parsed
again with that class given as the part-of-speech tag, which is what the parser's tagged input takes. A sentence refused for an unknown
word is tried once more with every class offered for it, and the grammar's syntax picks."""

import re
import sqlite3

from tolk import erg, lf
from tolk.rules import check, content
from tolk.sem import Reading

# The tag a lemma of a class takes, by the ending its form has: the other direction of content.TAGS.
TAG_OF: dict[tuple[str, str], tuple[str, ...]] = {}
for _tag, _class in content.TAGS.items():
    TAG_OF[_class] = TAG_OF.get(_class, ()) + (_tag.upper(),)


def remember(db: sqlite3.Connection, x: lf.LF, sentence: int) -> None:
    """The class of each unknown word a stored statement uses, from its first accepted use. A later use does not change it."""
    for a in check.atoms_of(x):
        m = lf.UNKNOWN_PRED.fullmatch(a.pred)
        if m:
            db.execute("INSERT OR IGNORE INTO word(lemma, pos, sentence) VALUES (?, ?, ?)", (m.group(1), m.group(2), sentence))


def tags_for(db: sqlite3.Connection, text: str) -> dict[str, tuple[str, ...]]:
    """Lowercase token to the tags of the word the store remembers it as: the lemma itself, or the lemma with a plural or third-person ending."""
    return tags_of(db.execute("SELECT lemma, pos FROM word").fetchall(), text)


def tags_of(known: list[tuple[str, str]], text: str) -> dict[str, tuple[str, ...]]:
    """The same for (lemma, class) pairs, class being n, v or a."""
    forms: dict[str, tuple[str, ...]] = {}
    for lemma, pos in known:
        for ending, suffix in (("", ""), ("s", "s"), ("es", "s")):
            forms[lemma + ending] = forms.get(lemma + ending, ()) + TAG_OF.get((pos, suffix), ())
    return {w.lower(): forms[w.lower()] for w, _, _ in erg.tokens(text) if w.lower() in forms and "'" not in text}


def parse(tags: dict[str, tuple[str, ...]], text: str, limit: int = erg.READINGS) -> list[erg.Parsed]:
    """The readings of a sentence, with the given class of each word the caller knows given to the parser. If that gives no reading the
    parser's own tagging stands."""
    return (erg.parse(text, tags, limit) if tags else []) or erg.parse(text, None, limit)


def fits(word: str, tag: str) -> bool:
    """Whether a word could be of the class this tag names: a tag with an s ending takes a word that has one, and the others a word that
    has none. A verb that ends like a past or progressive form is none of the classes the store can hold."""
    pos, suffix = content.TAGS[tag.lower()]
    return word.endswith("s") == bool(suffix) and not (pos == "v" and word.endswith(("ed", "ing")))


def lowercase_names(text: str, readings: list[Reading]) -> set[str]:
    """Words the readings given take for a name though the sentence spells them with a small letter: a word it lacks, or has only as a name."""
    return {w.lower() for r in readings for ep in r.eps if ep.pred == "named" and ep.cfrom >= 0 and text[ep.cfrom:ep.cfrom + 1].islower()
            for w in re.findall(r"\w+", text[ep.cfrom:ep.cto])}


def offered(text: str, readings: list[Reading], names: set[str] = frozenset()) -> list[erg.Parsed]:
    """The sentence parsed with every class offered for each word the grammar had to guess, or took for a name, so that the syntax of the
    sentence decides."""
    guessed = {m.group(1).lower() for r in readings for ep in r.eps if (m := content.UNKNOWN.fullmatch(ep.pred))} | names
    if not readings:  # the grammar gave no reading, so which word it lacks is not known: any small-letter word may be the one
        guessed |= {w.lower() for w, _, _ in erg.tokens(text) if w[0].islower() and w[0].isalpha()}
    tags = {w: tuple(t.upper() for t in content.TAGS if fits(w, t)) for w in guessed}
    return erg.parse(text, {w: t for w, t in tags.items() if t}) if tags and all(tags.values()) and "'" not in text else []

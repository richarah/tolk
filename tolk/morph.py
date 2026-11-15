"""Affixes of words the grammar does not know. An unknown word in a statement is split when stripping one affix, and undoing the simple
spelling changes, leaves a base that the store already has as a predicate of the right class. Otherwise the word stays whole.
The affixes are the one table below; they are not content words."""

import re
import sqlite3

from tolk import lf, store
from tolk.lf import Atom, Const, Var

# affix -> (where it attaches, class of the new word, class of its base, what it means in the store)
#   opposite: the word holds exactly when the base does not, as two strict rules that derive negative facts, one each way.
#   agent: a thing is one exactly when it does the verb, as two strict rules.
#   record: the split is recorded and no rule is added, since the store has no notion of possibility.
AFFIXES = {
    "un": ("prefix", "a", "a", "opposite"),
    "non": ("prefix", "a", "a", "opposite"),
    "er": ("suffix", "n", "v", "agent"),
    "able": ("suffix", "a", "v", "record"),
}
VOWELS = "aeiou"


def stems(word: str, affix: str) -> list[str]:
    """What the base may have been before the affix was added: itself, with a dropped e, with a doubled consonant, with y written i."""
    where = AFFIXES[affix][0]
    stem = word[len(affix):] if where == "prefix" else word[: -len(affix)]
    if where == "prefix" or len(stem) < 2:
        return [stem] if len(stem) >= 2 else []
    out = [stem, stem + "e"]
    if stem[-1] == stem[-2] and stem[-1] not in VOWELS:
        out.append(stem[:-1])
    if stem.endswith("i"):
        out.append(stem[:-1] + "y")
    return out


def split(lemma: str, pos: str, known: set[tuple[str, int]]) -> tuple[str, str] | None:
    """(base predicate, affix) for an unknown word of this class, if the store has the base."""
    for affix in sorted(AFFIXES, key=len, reverse=True):
        where, made, base_class, _ = AFFIXES[affix]
        if made != pos or not (lemma.startswith(affix) if where == "prefix" else lemma.endswith(affix)):
            continue
        for stem in stems(lemma, affix):
            pattern = re.compile(rf"_{re.escape(stem)}_{base_class}_.*")
            found = sorted(p for p, arity in known if arity == 2 and pattern.fullmatch(p))
            if found:
                return found[0], affix
    return None


def annotate(db: sqlite3.Connection, x: lf.Tell | lf.Rule) -> tuple[lf.Tell | lf.Rule, list[tuple[str, str, str]]]:
    """The statement with each new split shown as a note, and the splits (word predicate, base predicate, affix) to record once it is stored."""
    known = store.known_preds(db)
    done = {w for (w,) in db.execute("SELECT word FROM morph")}
    atoms = x.atoms if isinstance(x, lf.Tell) else x.head + x.body
    splits = []
    for pred in dict.fromkeys(a.pred for a in atoms):
        m = lf.UNKNOWN_PRED.fullmatch(pred)
        found = split(m.group(1), m.group(2), known) if m and pred not in done else None
        if found:
            splits.append((pred, found[0], found[1]))
    notes = tuple(shown(w, b, a) for w, b, a in splits)
    return (x.__class__(**{**x.__dict__, "notes": x.notes + notes}) if notes else x), splits


def shown(word: str, base: str, affix: str) -> str:
    return f"{_lemma(word)} = {affix} + {_lemma(base)}"


def _lemma(pred: str) -> str:
    return pred.lstrip("_").split("_")[0]


def record(db: sqlite3.Connection, splits: list[tuple[str, str, str]]) -> None:
    """The split, and what it means as rules, each with a sentence of its own so that a proof can name it."""
    x, e = Var("x"), Var("e1")
    for word, base, affix in splits:
        db.execute("INSERT OR IGNORE INTO morph(word, base, affix) VALUES (?, ?, ?)", (word, base, affix))
        meaning = AFFIXES[affix][3]

        if meaning == "opposite":
            none = Const("", lf.NO_EVENT)
            rules = [lf.Rule((Atom(base, (none, x), False),), (Atom(word, (e, x)),)), lf.Rule((Atom(word, (none, x), False),), (Atom(base, (e, x)),))]
        elif meaning == "agent":
            rules = [lf.Rule((Atom(base, (e, x)),), (Atom(word, (x,)),)), lf.Rule((Atom(word, (x,)),), (Atom(base, (e, x)),))]
        else:
            rules = []
        for rule, how in zip(rules, ("is {0} so not {1}", "is {1} so not {0}") if meaning == "opposite" else ("is one who {1}s", "{1}s so is one")):
            text = f"[axiom] {_lemma(word)} = {affix} + {_lemma(base)}: " + how.format(_lemma(word), _lemma(base))
            store.add_rule(db, rule, store.add_sentence(db, text))

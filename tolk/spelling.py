"""Spelling. The store keeps every name and every surface word it has accepted, with what each mapped to. A word a reading takes for a new
name, or for a word the grammar does not know, that is one edit from exactly one known word is refused as a possible typo, naming the word
and the candidate. tolk never corrects a word itself: a user who meant it sends the same sentence again."""

import re
import sqlite3

from tolk import lf, morph, store, words
from tolk.rules import content
from tolk.sem import Reading

MIN_LENGTH = 4  # a shorter word is never taken for a typo
LONG = 8  # a word this long may be two edits away


def distance(a: str, b: str) -> int:
    """Edits to turn a into b: insert, delete or replace a letter, or swap two adjacent letters (optimal string alignment)."""
    rows = [list(range(len(b) + 1))]
    for i, x in enumerate(a, 1):
        row = [i]
        for j, y in enumerate(b, 1):
            best = min(rows[i - 1][j] + 1, row[j - 1] + 1, rows[i - 1][j - 1] + (x != y))
            if i > 1 and j > 1 and x == b[j - 2] and a[i - 2] == y:
                best = min(best, rows[i - 2][j - 2] + 1)
            row.append(best)
        rows.append(row)
    return rows[-1][-1]


def allowed(word: str) -> int:
    return 2 if len(word) >= LONG else 1


def surfaces(text: str, r: Reading) -> dict[tuple[str, str], str]:
    """(word, kind) to what it mapped to, for each single word the reading's predications span: kind is name or word."""
    out: dict[tuple[str, str], str] = {}
    for ep in r.eps:
        found = re.findall(r"\w+", text[ep.cfrom:ep.cto]) if ep.cfrom >= 0 else []
        if len(found) != 1:
            continue
        if ep.pred == "named":
            out[(found[0].lower(), "name")] = ep.args.get("CARG", "").lower()
        else:
            out[(found[0].lower(), "word")] = ep.pred
    return out


def record(db: sqlite3.Connection, text: str, r: Reading) -> None:
    for (word, kind), maps_to in surfaces(text, r).items():
        db.execute("INSERT OR IGNORE INTO spelling(word, kind, maps_to) VALUES (?, ?, ?)", (word, kind, maps_to))


def check(db: sqlite3.Connection, text: str, r: Reading) -> lf.Refusal | None:
    """POSSIBLE_TYPO for the first new word that is near exactly one known word; None if there is none."""
    known = {w for (w,) in db.execute("SELECT word FROM spelling")} | {n for (n,) in db.execute("SELECT text FROM name")}
    remembered = words.tags_for(db, text)
    fresh = [w for (w, kind) in surfaces(text, r) if kind == "name" and w not in known]
    preds = store.known_preds(db)
    for ep in r.eps:  # a word the grammar lacks, unless it is a known word with an affix (the morphology table already reads it)
        m = content.UNKNOWN.fullmatch(ep.pred)
        if m and m.group(1).lower() not in known and not (m.group(2) in content.TAGS and morph.split(m.group(1).lower(), content.TAGS[m.group(2)][0], preds)):
            fresh.append(m.group(1).lower())
    for w in dict.fromkeys(fresh):
        if len(w) < MIN_LENGTH or w in remembered:
            continue
        near = sorted(k for k in known if k != w and distance(w, k) <= allowed(w))
        if len(near) == 1:
            return lf.Refusal("POSSIBLE_TYPO", f"{w}: did you mean {near[0]}?")
    return None

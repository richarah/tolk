"""What was said and when: the things sentences mention, and taking a sentence back."""

import sqlite3

from tolk import store


def add_mentions(db: sqlite3.Connection, sentence: int, mentions: list[tuple[int, str, str]]) -> None:
    db.executemany("INSERT INTO mention(sentence, position, entity, number) VALUES (?, ?, ?, ?)",
                   [(sentence, pos, ident, num) for pos, ident, num in mentions])


def recent_mentions(db: sqlite3.Connection) -> list[tuple[int, str, str]]:
    """(sentence, thing, number) of every mention, most recent first, with merged names followed to the thing they became."""
    rows = db.execute("SELECT sentence, entity, number FROM mention ORDER BY sentence DESC, position DESC").fetchall()
    return [(sent, store.canon(db, ident), num) for sent, ident, num in rows]


def retract(db: sqlite3.Connection, sentence: int, reason: str) -> None:
    """Remove what a sentence told: its facts' told source and its rules. The sentence row stays. Derived facts are for the caller to rebuild."""
    db.execute("DELETE FROM why WHERE sentence = ?", (sentence,))
    db.execute("DELETE FROM rule WHERE sentence = ?", (sentence,))
    db.execute("DELETE FROM mention WHERE sentence = ?", (sentence,))
    db.execute("DELETE FROM claim WHERE sentence = ?", (sentence,))
    db.execute("DELETE FROM fact WHERE id NOT IN (SELECT fact FROM why)")
    db.execute("INSERT INTO revision(sentence, reason) VALUES (?, ?)", (sentence, reason))


def latest_told(db: sqlite3.Connection, printed: str, ctx: str) -> tuple[int, str] | None:
    """The most recent sentence still in force whose printed logical form is this one: its id and text."""
    return db.execute(
        "SELECT id, text FROM sentence WHERE printed = ? AND ctx IN ('world', ?) AND ("
        "EXISTS (SELECT 1 FROM why WHERE sentence = sentence.id) OR EXISTS (SELECT 1 FROM rule WHERE sentence = sentence.id) "
        "OR EXISTS (SELECT 1 FROM merge WHERE sentence = sentence.id)) ORDER BY id DESC LIMIT 1", (printed, ctx)).fetchone()

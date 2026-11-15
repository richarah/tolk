"""The settings of a Mind that are kept in meta with the facts. Each has a default and a set of allowed values."""

import sqlite3

ALLOWED = {"closed_world": ("0", "1"), "wording": ("template", "generated")}
DEFAULT = {"closed_world": "0", "wording": "template"}


def get(db: sqlite3.Connection, key: str) -> str:
    row = db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else DEFAULT[key]


def put(db: sqlite3.Connection, key: str, value: str) -> None:
    if value not in ALLOWED[key]:
        raise ValueError(f"{key} must be one of {ALLOWED[key]}, not {value!r}")
    with db:
        db.execute("INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))

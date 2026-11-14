"""SQLite store: schema, writing told facts and rules, and identity of fresh constants."""

import sqlite3

from tolk import lf
from tolk.lf import Atom, Const, Var

SCHEMA = """
CREATE TABLE sentence(id INTEGER PRIMARY KEY, text TEXT NOT NULL);
CREATE TABLE entity(id TEXT PRIMARY KEY, kind TEXT NOT NULL);
CREATE TABLE name(entity TEXT NOT NULL, text TEXT NOT NULL);
CREATE UNIQUE INDEX name_u ON name(entity, text);
CREATE TABLE fact(
    id INTEGER PRIMARY KEY,
    pred TEXT NOT NULL, a0 TEXT NOT NULL, a1 TEXT NOT NULL, a2 TEXT NOT NULL,
    positive INTEGER NOT NULL, ctx TEXT NOT NULL, round INTEGER NOT NULL,
    UNIQUE(pred, a0, a1, a2, positive, ctx)
);
CREATE INDEX fact_pred ON fact(pred, positive, ctx);
CREATE TABLE why(
    fact INTEGER NOT NULL, sentence INTEGER, rule INTEGER, premises TEXT NOT NULL
);
CREATE UNIQUE INDEX why_u ON why(fact, IFNULL(sentence, 0), IFNULL(rule, 0), premises);
CREATE TABLE rule(
    id INTEGER PRIMARY KEY, sentence INTEGER NOT NULL, printed TEXT NOT NULL,
    lf TEXT NOT NULL, ran INTEGER
);
CREATE TABLE merge(kept TEXT NOT NULL, dropped TEXT NOT NULL, sentence INTEGER NOT NULL);
CREATE TABLE conflict(positive_fact INTEGER NOT NULL, negative_fact INTEGER NOT NULL);
"""


def open_store(path: str = ":memory:") -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    return db


def add_sentence(db: sqlite3.Connection, text: str) -> int:
    return db.execute("INSERT INTO sentence(text) VALUES (?)", (text,)).lastrowid


def current_round(db: sqlite3.Connection) -> int:
    return db.execute("SELECT COALESCE(MAX(round), 0) FROM fact").fetchone()[0]


def tell(db: sqlite3.Connection, t: lf.Tell, sentence: int, ctx: str = "world") -> list[int]:
    """Store ground atoms. Returns the ids of the facts this call added."""
    if db.execute("SELECT 1 FROM sentence WHERE text = (SELECT text FROM sentence WHERE id = ?) AND id < ?",
                  (sentence, sentence)).fetchone():
        return []  # a sentence already stored adds nothing; its events would otherwise be fresh again
    rnd = current_round(db) + 1
    ids = _fresh_ids(db, t)
    added = []
    for atom in t.atoms:
        ground = _ground(atom, ids)
        _entities(db, ground)
        pred, args = ground.pred, [c.id for c in ground.args] + [""] * (3 - len(ground.args))
        cur = db.execute(
            "INSERT OR IGNORE INTO fact(pred, a0, a1, a2, positive, ctx, round) VALUES (?, ?, ?, ?, 1, ?, ?)",
            (pred, *args, ctx, rnd),
        )
        if cur.rowcount:
            db.execute(
                "INSERT INTO why(fact, sentence, rule, premises) VALUES (?, ?, NULL, '[]')",
                (cur.lastrowid, sentence),
            )
            added.append(cur.lastrowid)
    return added


def add_rule(db: sqlite3.Connection, rule: lf.Rule, sentence: int) -> int:
    return db.execute(
        "INSERT INTO rule(sentence, printed, lf, ran) VALUES (?, ?, ?, NULL)",
        (sentence, lf.show(rule), lf.encode_rule(rule)),
    ).lastrowid


def known_preds(db: sqlite3.Connection) -> set[str]:
    return {row[0] for row in db.execute("SELECT DISTINCT pred FROM fact WHERE positive = 1")}


def _fresh_ids(db: sqlite3.Connection, t: lf.Tell) -> dict[str, str]:
    """Each fresh constant of a sentence gets an id no earlier sentence has used."""
    ids: dict[str, str] = {}
    for atom in t.atoms:
        for c in atom.args:
            if isinstance(c, Const) and c.kind in lf.FRESH and c.id not in ids:
                n = db.execute("SELECT COUNT(*) FROM entity WHERE kind = ?", (c.kind,)).fetchone()[0]
                while True:
                    n += 1
                    cand = lf.fresh_id(c.kind, n)
                    if not db.execute("SELECT 1 FROM entity WHERE id = ?", (cand,)).fetchone():
                        break
                ids[c.id] = cand
    return ids


def _ground(atom: Atom, ids: dict[str, str]) -> Atom:
    args = []
    for t in atom.args:
        if isinstance(t, Var):
            raise ValueError(f"told atom {atom.pred} has a variable {t.key}")
        args.append(Const(ids.get(t.id, t.id), t.kind))
    return Atom(atom.pred, tuple(args))


def _entities(db: sqlite3.Connection, atom: Atom) -> None:
    for c in atom.args:
        db.execute("INSERT OR IGNORE INTO entity(id, kind) VALUES (?, ?)", (c.id, c.kind))
        if c.kind == "named":
            db.execute("INSERT OR IGNORE INTO name(entity, text) VALUES (?, ?)", (c.id, c.id))

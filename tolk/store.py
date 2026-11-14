"""SQLite store: schema, writing told facts and rules, and identity of fresh constants."""

import json
import sqlite3

from tolk import lf
from tolk.lf import Atom, Const, Var

SCHEMA = """
CREATE TABLE sentence(id INTEGER PRIMARY KEY, text TEXT NOT NULL, printed TEXT NOT NULL DEFAULT '', ctx TEXT NOT NULL DEFAULT 'world');
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
CREATE TABLE mention(sentence INTEGER NOT NULL, position INTEGER NOT NULL, entity TEXT NOT NULL, number TEXT NOT NULL);
INSERT INTO entity(id, kind) VALUES ('user', 'named'), ('tolk', 'named');
INSERT INTO name(entity, text) VALUES ('user', 'user'), ('tolk', 'tolk');
"""


def open_store(path: str = ":memory:") -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    return db


def add_sentence(db: sqlite3.Connection, text: str, printed: str = "", ctx: str = "world") -> int:
    return db.execute("INSERT INTO sentence(text, printed, ctx) VALUES (?, ?, ?)", (text, printed, ctx)).lastrowid


def repeat_of(db: sqlite3.Connection, printed: str, ctx: str) -> tuple[int, str] | None:
    """An earlier sentence still in force whose printed logical form is this one: its id and text.
    In force means something it told, a rule or a merge, is still stored."""
    return db.execute(
        "SELECT id, text FROM sentence WHERE printed = ? AND ctx IN ('world', ?) AND ("
        "EXISTS (SELECT 1 FROM why WHERE sentence = sentence.id) OR EXISTS (SELECT 1 FROM rule WHERE sentence = sentence.id) "
        "OR EXISTS (SELECT 1 FROM merge WHERE sentence = sentence.id)) ORDER BY id LIMIT 1",
        (printed, ctx),
    ).fetchone()


def current_round(db: sqlite3.Connection) -> int:
    return db.execute("SELECT COALESCE(MAX(round), 0) FROM fact").fetchone()[0]


def tell(db: sqlite3.Connection, t: lf.Tell, sentence: int, ctx: str = "world") -> list[int] | lf.Refusal:
    """Store ground atoms. Returns the ids of the facts this call added, or a refusal if one contradicts a stored fact."""
    ids = _fresh_ids(db, t)
    grounds = [_ground(db, atom, ids) for atom in t.atoms]
    for g in grounds:
        opposite = _opposite(db, g, ctx)
        if opposite is not None:
            return lf.Refusal("CONTRADICTS", str(opposite))
    rnd = current_round(db) + 1
    added = []
    for g in grounds:
        _entities(db, g)
        pred, args = g.pred, [c.id for c in g.args] + [""] * (3 - len(g.args))
        cur = db.execute(
            "INSERT OR IGNORE INTO fact(pred, a0, a1, a2, positive, ctx, round) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pred, *args, int(g.positive), ctx, rnd),
        )
        if cur.rowcount:
            db.execute(
                "INSERT INTO why(fact, sentence, rule, premises) VALUES (?, ?, NULL, '[]')",
                (cur.lastrowid, sentence),
            )
            added.append(cur.lastrowid)
    return added


def merge(db: sqlite3.Connection, a: Const, b: Const, sentence: int) -> None:
    """Two names for one thing. The older entity is kept; the other's facts move onto it."""
    for c in (a, b):
        db.execute("INSERT OR IGNORE INTO entity(id, kind) VALUES (?, ?)", (c.id, c.kind))
    older = db.execute("SELECT id FROM entity WHERE id IN (?, ?) ORDER BY rowid LIMIT 1", (a.id, b.id)).fetchone()[0]
    dropped = b.id if older == a.id else a.id
    if dropped == older:
        return
    db.execute("INSERT INTO merge(kept, dropped, sentence) VALUES (?, ?, ?)", (older, dropped, sentence))
    db.execute("INSERT OR IGNORE INTO name(entity, text) VALUES (?, ?)", (older, dropped))
    db.execute("INSERT OR IGNORE INTO name(entity, text) VALUES (?, ?)", (older, older))
    for fid, pred, a0, a1, a2, positive, ctx, rnd in db.execute(
        "SELECT id, pred, a0, a1, a2, positive, ctx, round FROM fact "
        "WHERE a0 = ? OR a1 = ? OR a2 = ?", (dropped, dropped, dropped),
    ).fetchall():
        moved = [older if x == dropped else x for x in (a0, a1, a2)]
        twin = db.execute(
            "SELECT id FROM fact WHERE pred = ? AND a0 = ? AND a1 = ? AND a2 = ? AND positive = ? AND ctx = ?",
            (pred, *moved, positive, ctx),
        ).fetchone()
        if twin:
            db.execute("UPDATE why SET fact = ? WHERE fact = ?", (twin[0], fid))
            for why_id, premises in db.execute("SELECT rowid, premises FROM why").fetchall():
                listed = json.loads(premises)
                if fid in listed:
                    db.execute("UPDATE why SET premises = ? WHERE rowid = ?",
                               (json.dumps([twin[0] if p == fid else p for p in listed]), why_id))
            db.execute("DELETE FROM fact WHERE id = ?", (fid,))
        else:
            db.execute("UPDATE fact SET a0 = ?, a1 = ?, a2 = ? WHERE id = ?", (*moved, fid))


def canon(db: sqlite3.Connection, ident: str) -> str:
    """The entity an identifier now stands for, following merges."""
    row = db.execute("SELECT kept FROM merge WHERE dropped = ?", (ident,)).fetchone()
    return canon(db, row[0]) if row else ident


def derived_pairs(db: sqlite3.Connection) -> set[tuple[str, str]]:
    """(body predicate, head predicate) for every stored rule. A rule that already links two predicates is not proposed again."""
    pairs = set()
    for (text,) in db.execute("SELECT lf FROM rule"):
        r = lf.decode_rule(text)
        pairs |= {(b.pred, h.pred) for h in r.head for b in r.body}
    return pairs


def things_with(db: sqlite3.Connection, pred: str, ctx: str = "world") -> set[str]:
    """Known things with a positive fact of this predicate. A definite description matches these."""
    return {row[0] for row in db.execute(
        "SELECT DISTINCT a0 FROM fact WHERE pred = ? AND positive = 1 AND ctx IN ('world', ?) AND a0 != ''",
        (pred, ctx))}


def drop_ctx(db: sqlite3.Connection, ctx: str) -> None:
    """Remove a supposition's facts, their proofs and conflicts, and the fresh things nothing else uses."""
    ids = "SELECT id FROM fact WHERE ctx = ?"
    db.execute(f"DELETE FROM conflict WHERE positive_fact IN ({ids}) OR negative_fact IN ({ids})", (ctx, ctx))
    db.execute(f"DELETE FROM why WHERE fact IN ({ids})", (ctx,))
    db.execute("DELETE FROM fact WHERE ctx = ?", (ctx,))
    db.execute(
        "DELETE FROM sentence WHERE id NOT IN (SELECT sentence FROM why WHERE sentence IS NOT NULL "
        "UNION SELECT sentence FROM rule UNION SELECT sentence FROM merge)"
    )
    db.execute("DELETE FROM mention WHERE sentence NOT IN (SELECT id FROM sentence)")
    db.execute(
        "DELETE FROM entity WHERE kind IN ('event', 'anon', 'skolem') AND id NOT IN ("
        "SELECT a0 FROM fact UNION SELECT a1 FROM fact UNION SELECT a2 FROM fact)"
    )


def add_rule(db: sqlite3.Connection, rule: lf.Rule, sentence: int) -> int:
    return db.execute(
        "INSERT INTO rule(sentence, printed, lf, ran) VALUES (?, ?, ?, NULL)",
        (sentence, lf.show(rule), lf.encode_rule(rule)),
    ).lastrowid


def known_preds(db: sqlite3.Connection) -> set[tuple[str, int]]:
    """Predicate and arity of each stored positive fact; the empty event column is not counted."""
    return {(pred, n) for pred, n in db.execute(
        "SELECT DISTINCT pred, (a0 != '') + (a1 != '') + (a2 != '') FROM fact WHERE positive = 1")}


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
                    if cand not in ids.values() and not db.execute("SELECT 1 FROM entity WHERE id = ?", (cand,)).fetchone():
                        break
                ids[c.id] = cand
    return ids


def _ground(db: sqlite3.Connection, atom: Atom, ids: dict[str, str]) -> Atom:
    args = []
    for t in atom.args:
        if isinstance(t, Var):
            raise ValueError(f"told atom {atom.pred} has a variable {t.key}")
        ident = ids.get(t.id, t.id)
        args.append(Const(ident if t.kind in lf.FRESH else canon(db, ident), t.kind))
    return Atom(atom.pred, tuple(args), atom.positive)


def _opposite(db: sqlite3.Connection, g: Atom, ctx: str) -> int | None:
    """A stored or derived fact that says the opposite of ground atom g. An empty event matches any event."""
    a0, a1, a2 = (g.args + (Const(""),) * 3)[:3]
    row = db.execute(
        "SELECT id FROM fact WHERE pred = ? AND positive = ? AND ctx = ? AND a1 = ? AND a2 = ? "
        "AND (a0 = ? OR a0 = '' OR ? = '') LIMIT 1",
        (g.pred, int(not g.positive), ctx, a1.id, a2.id, a0.id, a0.id),
    ).fetchone()
    return row[0] if row else None


def _entities(db: sqlite3.Connection, atom: Atom) -> None:
    for c in atom.args:
        if c.kind == lf.NO_EVENT:
            continue
        db.execute("INSERT OR IGNORE INTO entity(id, kind) VALUES (?, ?)", (c.id, c.kind))
        if c.kind == "named":
            db.execute("INSERT OR IGNORE INTO name(entity, text) VALUES (?, ?)", (c.id, c.id))


def mentioning(db: sqlite3.Connection, entity: str, ctx: str = "world") -> list[tuple[int, bool]]:
    """Facts that mention a thing, or that modify an event the thing takes part in, as (id, told). Told facts come first."""
    ident = canon(db, entity)
    rows = db.execute(
        "SELECT f.id, EXISTS (SELECT 1 FROM why w WHERE w.fact = f.id AND w.sentence IS NOT NULL) AS told FROM fact f "
        "WHERE f.ctx IN ('world', ?) AND (? IN (f.a0, f.a1, f.a2) OR f.a0 IN ("
        "  SELECT g.a0 FROM fact g JOIN entity e ON e.id = g.a0 WHERE e.kind = 'event' AND ? IN (g.a1, g.a2))) "
        "ORDER BY told DESC, f.id",
        (ctx, ident, ident),
    ).fetchall()
    return [(fid, bool(told)) for fid, told in rows]


def add_mentions(db: sqlite3.Connection, sentence: int, mentions: list[tuple[int, str, str]]) -> None:
    db.executemany("INSERT INTO mention(sentence, position, entity, number) VALUES (?, ?, ?, ?)",
                   [(sentence, pos, ident, num) for pos, ident, num in mentions])


def recent_mentions(db: sqlite3.Connection) -> list[tuple[int, str, str]]:
    """(sentence, thing, number) of every mention, most recent first, with merged names followed to the thing they became."""
    rows = db.execute("SELECT sentence, entity, number FROM mention ORDER BY sentence DESC, position DESC").fetchall()
    return [(sent, canon(db, ident), num) for sent, ident, num in rows]


def fresh_of_kind(db: sqlite3.Connection, kind: str) -> list[str]:
    return [i for (i,) in db.execute("SELECT id FROM entity WHERE kind = ? ORDER BY rowid", (kind,))]

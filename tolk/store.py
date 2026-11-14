"""SQLite store: schema, writing told facts and rules, and identity of fresh constants."""

import dataclasses
import json
import sqlite3

from tolk import lf
from tolk.lf import Atom, Const, Var

SCHEMA = """
CREATE TABLE sentence(id INTEGER PRIMARY KEY, text TEXT NOT NULL, printed TEXT NOT NULL DEFAULT '', ctx TEXT NOT NULL DEFAULT 'world',
    trust INTEGER NOT NULL DEFAULT 0, observation INTEGER NOT NULL DEFAULT 0);
CREATE TABLE entity(id TEXT PRIMARY KEY, kind TEXT NOT NULL);
CREATE TABLE name(entity TEXT NOT NULL, text TEXT NOT NULL);
CREATE UNIQUE INDEX name_u ON name(entity, text);
CREATE TABLE fact(
    id INTEGER PRIMARY KEY,
    pred TEXT NOT NULL, a0 TEXT NOT NULL, a1 TEXT NOT NULL, a2 TEXT NOT NULL,
    positive INTEGER NOT NULL, ctx TEXT NOT NULL, round INTEGER NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,  -- 1 told, 2 derived by strict rules only, 3 a default was used
    UNIQUE(pred, a0, a1, a2, positive, ctx)
);
CREATE INDEX fact_pred ON fact(pred, positive, ctx);
CREATE TABLE why(
    fact INTEGER NOT NULL, sentence INTEGER, rule INTEGER, premises TEXT NOT NULL, bindings TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX why_u ON why(fact, IFNULL(sentence, 0), IFNULL(rule, 0), premises);
CREATE TABLE rule(
    id INTEGER PRIMARY KEY, sentence INTEGER NOT NULL, printed TEXT NOT NULL,
    lf TEXT NOT NULL, ran INTEGER, kind TEXT NOT NULL DEFAULT 'strict'
);
CREATE TABLE merge(kept TEXT NOT NULL, dropped TEXT NOT NULL, sentence INTEGER NOT NULL);
CREATE TABLE conflict(positive_fact INTEGER NOT NULL, negative_fact INTEGER NOT NULL);
CREATE TABLE defeat(rule INTEGER NOT NULL, bindings TEXT NOT NULL, by_fact INTEGER NOT NULL, reason TEXT NOT NULL);
CREATE UNIQUE INDEX defeat_u ON defeat(rule, bindings);
CREATE TABLE revision(sentence INTEGER NOT NULL, reason TEXT NOT NULL);
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE mention(sentence INTEGER NOT NULL, position INTEGER NOT NULL, entity TEXT NOT NULL, number TEXT NOT NULL);
INSERT INTO entity(id, kind) VALUES ('user', 'named'), ('tolk', 'named');
INSERT INTO name(entity, text) VALUES ('user', 'user'), ('tolk', 'tolk');
"""


def open_store(path: str = ":memory:") -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    return db


def add_sentence(db: sqlite3.Connection, text: str, printed: str = "", ctx: str = "world", trust: int = 0, observation: bool = False) -> int:
    return db.execute("INSERT INTO sentence(text, printed, ctx, trust, observation) VALUES (?, ?, ?, ?, ?)",
                      (text, printed, ctx, trust, int(observation))).lastrowid


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


def tell(db: sqlite3.Connection, t: lf.Tell, sentence: int, ctx: str = "world", allow_conflict: bool = False) -> list[int] | lf.Refusal:
    """Store ground atoms. Returns the ids of the facts this call added, or a refusal if one contradicts a stored fact.
    An observation may contradict one: it is stored, and the clash is a conflict to resolve."""
    ids = _fresh_ids(db, t)
    grounds = [_ground(db, atom, ids) for atom in t.atoms]
    for g in grounds:
        opposite = _opposite(db, g, ctx)
        if opposite is not None and not allow_conflict:
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
            fact_id = cur.lastrowid
            added.append(fact_id)
        else:
            # Already stored, perhaps only derived: it is told now, and a rebuild of the derived facts must keep it.
            (fact_id,) = db.execute("SELECT id FROM fact WHERE pred = ? AND a0 = ? AND a1 = ? AND a2 = ? AND positive = ? AND ctx = ?",
                                    (pred, *args, int(g.positive), ctx)).fetchone()
            db.execute("UPDATE fact SET level = 1 WHERE id = ?", (fact_id,))
        db.execute("INSERT OR IGNORE INTO why(fact, sentence, rule, premises) VALUES (?, ?, NULL, '[]')", (fact_id, sentence))
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
        "INSERT INTO rule(sentence, printed, lf, ran, kind) VALUES (?, ?, ?, NULL, ?)",
        (sentence, lf.show(rule), lf.encode_rule(rule), rule.kind),
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
        # Only a thing the sentence itself creates is renumbered; an id that only resembles one is a thing already stored.
        args.append(Const(ids[t.id], t.kind) if t.kind in lf.FRESH else Const(canon(db, t.id), t.kind))
    return Atom(atom.pred, tuple(args), atom.positive)


def _opposite(db: sqlite3.Connection, g: Atom, ctx: str) -> int | None:
    """A stored or derived fact that says the opposite of ground atom g. An empty event matches any event."""
    a0, a1, a2 = (g.args + (Const(""),) * 3)[:3]
    row = db.execute(
        "SELECT id FROM fact WHERE pred = ? AND positive = ? AND ctx = ? AND a1 = ? AND a2 = ? "
        "AND (a0 = ? OR a0 = '' OR ? = '') AND level <= 2 LIMIT 1",
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


def ensure_time_axioms(db: sqlite3.Connection) -> None:
    """The built-in axioms about order, stored as rules with a sentence each, so that a proof can name them.
    Made when the first ordering or year is told, so a store that never mentions time has none."""
    if db.execute("SELECT 1 FROM meta WHERE key = 'time_axioms'").fetchone():
        return
    x, y, z, e1, e2 = (Var(n) for n in ("x", "y", "z", "e1", "e2"))
    before = lambda a, b, pos=True: Atom(lf.BEFORE, (a, b), pos)
    axioms = [
        ("[axiom] before is transitive", lf.Rule((before(x, z),), (before(x, y), before(y, z))), "strict"),
        ("[axiom] before is asymmetric", lf.Rule((before(y, x, False),), (before(x, y),)), "strict"),
        ("[axiom] an event in an earlier year is before an event in a later year",
         lf.Rule((before(e1, e2),), (Atom("_in_p_temp", (e1, Var("y1"))), Atom("_in_p_temp", (e2, Var("y2"))))), "axiom"),
    ]
    for text, rule, kind in axioms:
        sid = add_sentence(db, text)
        db.execute("INSERT INTO rule(sentence, printed, lf, ran, kind) VALUES (?, ?, ?, NULL, ?)", (sid, text, lf.encode_rule(rule), kind))
    db.execute("INSERT INTO meta(key, value) VALUES ('time_axioms', '1')")


def reuse_events(db: sqlite3.Connection, t: lf.Tell, ctx: str) -> lf.Tell:
    """An event that an ordering mentions is the event an earlier sentence told, if that one has exactly the same content, so that
    orderings chain: in "A before B" and "B before C" the two B are one event. Other events stay fresh, as a repeated sentence adds nothing."""
    ordered = {x for a in t.atoms if a.pred == lf.BEFORE for x in a.args if isinstance(x, Const) and x.kind == "event"}
    swap: dict[Const, Const] = {}
    for e in sorted(ordered, key=lambda c: c.id):
        about = [a for a in t.atoms if a.pred != lf.BEFORE and a.args and a.args[0] == e]
        if not about or any(isinstance(x, Const) and x.kind in lf.FRESH for a in about for x in a.args[1:]):
            continue
        for (cand,) in db.execute("SELECT DISTINCT a0 FROM fact WHERE pred = ? AND ctx IN ('world', ?) AND a0 != ''", (about[0].pred, ctx)).fetchall():
            if all(_has(db, a, cand, ctx) for a in about) and Const(cand, "named") not in swap.values():
                swap[e] = Const(cand, "named")
                break
    if not swap:
        return t
    return dataclasses.replace(t, atoms=tuple(
        Atom(a.pred, tuple(swap.get(x, x) if isinstance(x, Const) else x for x in a.args), a.positive) for a in t.atoms))


def _has(db: sqlite3.Connection, a: Atom, event: str, ctx: str) -> bool:
    rest = [x.id for x in a.args[1:] if isinstance(x, Const)]
    rest += [""] * (2 - len(rest))
    return db.execute("SELECT 1 FROM fact WHERE pred = ? AND a0 = ? AND a1 = ? AND a2 = ? AND positive = ? AND ctx IN ('world', ?)",
                      (a.pred, event, rest[0], rest[1], int(a.positive), ctx)).fetchone() is not None


def add_mentions(db: sqlite3.Connection, sentence: int, mentions: list[tuple[int, str, str]]) -> None:
    db.executemany("INSERT INTO mention(sentence, position, entity, number) VALUES (?, ?, ?, ?)",
                   [(sentence, pos, ident, num) for pos, ident, num in mentions])


def recent_mentions(db: sqlite3.Connection) -> list[tuple[int, str, str]]:
    """(sentence, thing, number) of every mention, most recent first, with merged names followed to the thing they became."""
    rows = db.execute("SELECT sentence, entity, number FROM mention ORDER BY sentence DESC, position DESC").fetchall()
    return [(sent, canon(db, ident), num) for sent, ident, num in rows]


def fresh_of_kind(db: sqlite3.Connection, kind: str) -> list[str]:
    return [i for (i,) in db.execute("SELECT id FROM entity WHERE kind = ? ORDER BY rowid", (kind,))]


def retract(db: sqlite3.Connection, sentence: int, reason: str) -> None:
    """Remove what a sentence told: its facts' told source and its rules. The sentence row stays. Derived facts are for the caller to rebuild."""
    db.execute("DELETE FROM why WHERE sentence = ?", (sentence,))
    db.execute("DELETE FROM rule WHERE sentence = ?", (sentence,))
    db.execute("DELETE FROM mention WHERE sentence = ?", (sentence,))
    db.execute("DELETE FROM fact WHERE id NOT IN (SELECT fact FROM why)")
    db.execute("INSERT INTO revision(sentence, reason) VALUES (?, ?)", (sentence, reason))


def latest_told(db: sqlite3.Connection, printed: str, ctx: str) -> tuple[int, str] | None:
    """The most recent sentence still in force whose printed logical form is this one: its id and text."""
    return db.execute(
        "SELECT id, text FROM sentence WHERE printed = ? AND ctx IN ('world', ?) AND ("
        "EXISTS (SELECT 1 FROM why WHERE sentence = sentence.id) OR EXISTS (SELECT 1 FROM rule WHERE sentence = sentence.id) "
        "OR EXISTS (SELECT 1 FROM merge WHERE sentence = sentence.id)) ORDER BY id DESC LIMIT 1", (printed, ctx)).fetchone()

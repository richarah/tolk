"""Defaults and the conflict policy. Derived facts are a cache over told facts and rules; this module rebuilds that cache.

Strength, strongest first: 1 a told fact, 2 a fact derived by strict rules only, 3 a fact whose derivation used a default.
A level 3 fact loses to anything stronger. Two level 3 facts are separated by the policy, an ordered list of criteria."""

import json
import sqlite3

from tolk import engine, lf, store
from tolk.lf import Atom, Const, Var

POLICIES = ("specific", "trusted", "recent")


def has_defaults(db: sqlite3.Connection) -> bool:
    return db.execute("SELECT 1 FROM rule WHERE kind = 'default' LIMIT 1").fetchone() is not None


def refresh(db: sqlite3.Connection, ctx: str, policy: tuple[str, ...]) -> None:
    """Bring the derived facts up to date. With no default rule a plain run adds to them; otherwise they are rebuilt."""
    if has_defaults(db) or db.execute("SELECT 1 FROM fact WHERE level = 3 LIMIT 1").fetchone():
        rebuild(db, ctx, policy)
    else:
        engine.run(db, ctx)


def rebuild(db: sqlite3.Connection, ctx: str, policy: tuple[str, ...]) -> None:
    """Strict closure, then the default closure on top, skipping defeated instances; decide each clash and defeat the loser;
    start the default closure again while the set of defeats grows. It only grows, so this ends."""
    contexts = ["world"] + ([ctx] if ctx != "world" else [])
    db.execute("DELETE FROM why WHERE rule IS NOT NULL")
    db.execute("DELETE FROM fact WHERE id NOT IN (SELECT fact FROM why)")
    db.execute("UPDATE fact SET level = 1")
    db.execute("DELETE FROM conflict")
    db.execute("DELETE FROM defeat")
    for c in contexts:
        _reset(db)
        engine.run(db, c)
    winners: dict[tuple[int, str], tuple] = {}
    while True:
        db.execute("DELETE FROM why WHERE fact IN (SELECT id FROM fact WHERE level = 3)")
        db.execute("DELETE FROM fact WHERE level = 3 AND id NOT IN (SELECT fact FROM why)")
        db.execute("DELETE FROM conflict")
        _reset(db)
        for c in contexts:
            engine.run(db, c, ("strict", "default"))
        if not _decide(db, policy, winners):
            break
    for (rule, bindings, dctx), sig in winners.items():
        db.execute("UPDATE defeat SET by_fact = (SELECT id FROM fact WHERE pred = ? AND a0 = ? AND a1 = ? AND a2 = ? AND positive = ? AND ctx = ?) "
                   "WHERE rule = ? AND bindings = ? AND ctx = ?", (*sig, rule, bindings, dctx))
    engine.record_conflicts(db)


def _reset(db: sqlite3.Connection) -> None:
    db.execute("UPDATE rule SET ran = NULL")


def _decide(db: sqlite3.Connection, policy: tuple[str, ...], winners: dict) -> bool:
    """Defeat the loser of each clash that has one. True if that defeated something new."""
    grew = False
    clashes = db.execute(f"SELECT p.id, n.id, p.level, n.level, p.pred, p.ctx, n.ctx {engine.CROSS} AND (p.level = 3 OR n.level = 3)").fetchall()
    for pid, nid, lp, ln, pred, pctx, nctx in clashes:
        # A clash between the world and a supposition is decided for the supposition: the defeat belongs to it.
        dctx = nctx if pctx == "world" else pctx
        if lp != ln:
            win, lose = (pid, nid) if lp < ln else (nid, pid)
            reason = "told fact" if min(lp, ln) == 1 else "strict rules"
            blocked = _defaults_of(db, lose)
        else:
            a, b = (_defaults_of(db, pid) or [None])[0], (_defaults_of(db, nid) or [None])[0]
            if a is None or b is None:
                continue
            verdict = _separate(db, policy, a[0], b[0], pred)
            if verdict is None:
                continue
            first_wins, reason = verdict
            win, lose = (pid, nid) if first_wins else (nid, pid)
            blocked = [b if first_wins else a]
        for rule, bindings in blocked:
            cur = db.execute("INSERT OR IGNORE INTO defeat(rule, bindings, by_fact, reason, ctx) VALUES (?, ?, ?, ?, ?)",
                             (rule, bindings, win, reason, dctx))
            if cur.rowcount:
                grew = True
                winners[(rule, bindings, dctx)] = db.execute("SELECT pred, a0, a1, a2, positive, ctx FROM fact WHERE id = ?", (win,)).fetchone()
    return grew


def _defaults_of(db: sqlite3.Connection, fact_id: int) -> list[tuple[int, str]]:
    """The default rule instances in the first derivation of a fact, the topmost first."""
    row = db.execute("SELECT rule, premises, bindings FROM why WHERE fact = ? AND rule IS NOT NULL ORDER BY rowid LIMIT 1", (fact_id,)).fetchone()
    if row is None:
        return []
    rule, premises, bindings = row
    kind = db.execute("SELECT kind FROM rule WHERE id = ?", (rule,)).fetchone()[0]
    out = [(rule, bindings)] if kind == "default" else []
    for p in json.loads(premises):
        out += _defaults_of(db, p)
    return out


def _separate(db: sqlite3.Connection, policy: tuple[str, ...], a: int, b: int, pred: str) -> tuple[bool, str] | None:
    """Which of two default rules wins, by the first criterion in the policy that separates them: (first wins, criterion)."""
    if a == b:
        return None
    for criterion in policy:
        if criterion == "specific":
            ab, ba = implies(db, a, b, pred), implies(db, b, a, pred)
            if ab != ba:
                return ab, criterion
        else:
            ka, kb = _rank(db, criterion, a), _rank(db, criterion, b)
            if ka != kb:
                return ka > kb, criterion
    return None


def _rank(db: sqlite3.Connection, criterion: str, rule: int) -> int:
    """Trust of the sentence a rule came from, or the order of that sentence: higher wins."""
    column = "trust" if criterion == "trusted" else "id"
    return db.execute(f"SELECT s.{column} FROM rule r JOIN sentence s ON s.id = r.sentence WHERE r.id = ?", (rule,)).fetchone()[0]


def implies(db: sqlite3.Connection, a: int, b: int, pred: str) -> bool:
    """Rule a is more specific than rule b if a's body, asserted about a fresh thing, brings b's body with it by strict rules.
    The two rules clash over pred, so the things in their heads are the same thing: b's body is read about a's."""
    ra, rb = (_rule(db, r) for r in (a, b))
    ha, hb = (next(h for h in r.head if h.pred == pred) for r in (ra, rb))
    same = {tb: ta for ta, tb in zip(ha.args, hb.args) if isinstance(tb, Var) and not tb.event}
    goal = tuple(Atom(x.pred, tuple(same.get(t, Var(t.key + "'") if isinstance(t, Var) else t) if isinstance(t, Var) else t for t in x.args), x.positive)
                 for x in rb.body)
    return entails(db, ra.body, goal)


def _rule(db: sqlite3.Connection, rule_id: int) -> lf.Rule:
    return lf.decode_rule(db.execute("SELECT lf FROM rule WHERE id = ?", (rule_id,)).fetchone()[0])


def scratch(db: sqlite3.Connection, body: tuple[Atom, ...], kinds: tuple[str, ...], ctx: str = "world") -> tuple[sqlite3.Connection, dict[Var, Const]]:
    """A store with only the rules of the given kinds that apply in this context, and the body asserted about fresh things."""
    other = store.open_store()
    sid = store.add_sentence(other, "scratch")
    rows = db.execute("SELECT kind, lf, sentence FROM rule WHERE kind IN ({}) AND ctx IN ('world', ?) ORDER BY id".format(", ".join("?" * len(kinds))),
                      (*kinds, ctx))
    for kind, text, sentence in rows:
        other.execute("INSERT INTO rule(sentence, printed, lf, ran, kind) VALUES (?, '', ?, NULL, ?)", (sid, text, kind))
    things: dict[Var, Const] = {}
    for a in body:
        for t in a.args:
            if isinstance(t, Var) and t not in things:
                things[t] = Const(f"fresh{len(things)}", "event" if t.event else "named")
    asserted = tuple(Atom(a.pred, tuple(things.get(t, t) if isinstance(t, Var) else t for t in a.args), a.positive) for a in body if a.positive)
    store.tell(other, lf.Tell(asserted), sid)
    return other, things


def entails(db: sqlite3.Connection, body: tuple[Atom, ...], goal: tuple[Atom, ...]) -> bool:
    """Does the goal follow from the body by strict rules alone, for fresh things? Known facts are never used."""
    other, things = scratch(db, body, ("strict",))
    engine.run(other)
    return _holds(other, goal, things)


def _holds(other: sqlite3.Connection, goal: tuple[Atom, ...], things: dict[Var, Const]) -> bool:
    """Whether the goal has a match in the store. Variables the body shared with it are the fresh things."""
    bound = tuple(Atom(a.pred, tuple(things.get(t, t) if isinstance(t, Var) else t for t in a.args), a.positive) for a in goal)
    m = engine.Match(bound, "world", None, None)
    return other.execute(f"SELECT 1 {m.src} LIMIT 1", m.params).fetchone() is not None


def universal(db: sqlite3.Connection, every: lf.Every, policy: tuple[str, ...], ctx: str = "world") -> tuple[str, bool]:
    """Is every one of these so? Assert the restriction about a fresh thing, derive with every rule, and see what follows.
    Returns (Yes, No, Unknown or Conflict, by default). Known instances are never evidence."""
    other, things = scratch(db, every.body, ("strict", "default"), ctx)
    rebuild(other, "world", policy)
    claim = _strength(other, every.head, things, flip=False)
    against = _strength(other, every.head, things, flip=True)
    if claim <= 2 and against <= 2:
        return "Conflict", False
    if claim <= 3 and claim < against:
        return "Yes", claim == 3
    if against <= 3 and against < claim:
        return "No", against == 3
    return "Unknown", False


def _strength(other: sqlite3.Connection, goal: tuple[Atom, ...], things: dict[Var, Const], flip: bool) -> int:
    """The level of the strongest way the goal holds, or 4 if it does not. flip asks for the opposite of every atom."""
    atoms = tuple(Atom(a.pred, tuple(things.get(t, t) if isinstance(t, Var) else t for t in a.args)) for a in goal)
    polarity = tuple(int(a.positive) ^ int(flip) for a in goal)
    m = engine.Match(atoms, "world", None, None, polarity)
    levels = [f"{i[:-3]}.level" for i in m.ids_list]
    row = other.execute(f"SELECT MIN(MAX(1, {', '.join(levels)})) {m.src}", m.params).fetchone()
    return row[0] if row and row[0] is not None else 4

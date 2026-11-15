"""What a kind is: the rules that mention its predicate, the things of that kind, and what was told about the kind itself."""

import re
import sqlite3

from tolk import say, store

CLASS = re.compile(r"_([^_]+)_([nva])_")
NAME = {"n": "noun", "v": "verb", "a": "adjective"}


def describe(db: sqlite3.Connection, ctx: str, pred: str) -> str:
    m = CLASS.match(pred)
    if m is None:
        return "Unknown"
    lemma, cls = m.groups()
    used, preds = cls, _stored(db, lemma, cls)
    lines = []
    if not preds:
        # A word with no predicate in the class asked is looked for in another class. Only this description uses the link.
        used, preds = next(((c, p) for c in "nva" if c != cls and (p := _stored(db, lemma, c))), (cls, []))
        if not preds:
            return "Unknown"
        lines.append(f"(widened: {lemma} ({NAME[cls]}) matched as {lemma} ({NAME[used]}))")
    rules = _rules(db, preds)
    if rules:
        lines += ["Rules:"] + [f'  "{text}"' + ("  (default)" if kind == "default" else "") for text, kind in rules]
    found = _things(db, ctx, preds) if used == "n" else _facts(db, ctx, preds)
    if found:
        lines.append(f"Known: {len(found)}: " + ", ".join(shown for shown in found[:10]))
    about = store.mentioning(db, lemma, ctx) if db.execute("SELECT 1 FROM entity WHERE id = ?", (lemma,)).fetchone() else []
    if about:
        lines.append("Facts about it:")
        lines += [f"  {say.fact_line(db, fid)}" for fid, _ in about]
    return "\n".join(lines) or "Unknown"


def _stored(db: sqlite3.Connection, lemma: str, cls: str) -> list[str]:
    """Predicates of this lemma and class that a fact or a rule uses."""
    prefix = f"_{lemma}_{cls}_"
    preds = {p for (p,) in db.execute("SELECT DISTINCT pred FROM fact WHERE substr(pred, 1, ?) = ?", (len(prefix), prefix))}
    pattern = re.compile(r"(?<![\w+])" + re.escape(prefix) + r"[^\s(,]*\(")
    for (printed,) in db.execute("SELECT printed FROM rule"):
        preds |= {x[:-1] for x in pattern.findall(printed)}
    return sorted(preds)


def _rules(db: sqlite3.Connection, preds: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for printed, kind, text in db.execute("SELECT r.printed, r.kind, s.text FROM rule r JOIN sentence s ON s.id = r.sentence ORDER BY r.id"):
        if text.startswith("[axiom]") or not any(re.search(r"(?<![\w+])" + re.escape(p) + r"\(", printed) for p in preds):
            continue
        if (text, kind) not in out:
            out.append((text, kind))
    return out


def _things(db: sqlite3.Connection, ctx: str, preds: list[str]) -> list[str]:
    rows = db.execute(f"SELECT DISTINCT a0 FROM fact WHERE positive = 1 AND a0 != '' AND ctx IN ('world', ?) "
                      f"AND pred IN ({', '.join('?' * len(preds))}) ORDER BY a0", (ctx, *preds)).fetchall()
    named = {i for (i,) in db.execute("SELECT id FROM entity WHERE kind = 'named'")}
    return [say.SPEAKERS.get(a) or a.replace("_", " ").title() if a in named else f"an unnamed thing ({a})" for (a,) in rows]


def _facts(db: sqlite3.Connection, ctx: str, preds: list[str]) -> list[str]:
    rows = db.execute(f"SELECT f.id, s.text FROM fact f JOIN why w ON w.fact = f.id AND w.sentence IS NOT NULL JOIN sentence s ON s.id = w.sentence "
                      f"WHERE f.positive = 1 AND f.ctx IN ('world', ?) AND f.pred IN ({', '.join('?' * len(preds))}) GROUP BY f.id ORDER BY f.id", (ctx, *preds)).fetchall()
    return [f'{say.fact_line(db, fid)}  (told: "{text}")' for fid, text in rows]

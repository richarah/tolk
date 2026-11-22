"""Answers, descriptions and proofs as the text a person reads."""

import dataclasses
import sqlite3

from tolk import lf, morph, say, store
from tolk.ask import Answer, prove
from tolk.lf import Atom
from tolk.rules import claims


def describe(db: sqlite3.Connection, ctx: str, entity: str) -> str:
    facts = store.mentioning(db, entity, ctx)
    if not facts:
        return "Unknown"
    lines = []
    for fid, told in facts:
        p = prove(db, fid)
        source = f'told: "{db.execute("SELECT text FROM sentence WHERE id = ?", (p.sentence,)).fetchone()[0]}"' if told and p.sentence else f"by rule {p.rule}"
        lines.append(f"{say.fact_line(db, fid)}  ({source})")
    preds = [p for (p,) in db.execute(f"SELECT DISTINCT pred FROM fact WHERE id IN ({', '.join('?' * len(facts))})", [f for f, _ in facts])]
    for word, base, affix in db.execute(f"SELECT word, base, affix FROM morph WHERE word IN ({', '.join('?' * len(preds))})", preds):
        lines.append(f"({morph.shown(word, base, affix)})")
    return "\n".join(lines)


def defeated(db: sqlite3.Connection, proofs: list) -> str:
    """Lines for each default rule instance that a fact in these proofs defeated, and by which criterion."""
    facts: list[int] = []

    def walk(p) -> None:
        facts.append(p.fact)
        for q in p.premises:
            walk(q)

    for p in proofs:
        walk(p)
    if not facts:
        return ""
    marks = ", ".join("?" * len(facts))
    rows = db.execute(
        f"SELECT d.rule, d.reason, d.by_fact, s.text FROM defeat d JOIN rule r ON r.id = d.rule JOIN sentence s ON s.id = r.sentence "
        f"WHERE d.by_fact IN ({marks}) GROUP BY d.rule, d.reason ORDER BY d.rule", facts).fetchall()
    return "\n".join(f'  defeated "{text}" (rule {rule}) by {reason}' for rule, reason, _, text in rows)


def _held(db: sqlite3.Connection, content) -> list[str]:
    return [i for (i,) in db.execute("SELECT id FROM claim WHERE printed = ?", (claims.claim_key(content),))]


def _bind(atoms, var, claim: str) -> tuple[Atom, ...]:
    return tuple(Atom(a.pred, tuple(lf.Const(claim, "claim") if t == var else t for t in a.args), a.positive) for a in atoms)


def bind_claims(db: sqlite3.Connection, x: lf.Ask) -> lf.Ask | Answer:
    """A question about what someone believes: the claims whose content is exactly the asked content stand in for the claim variable.
    Several claims joined by and need each to be held (any choice of held claims for them); joined by or, any one of them."""
    if len(x.claims) == 1:
        (var, content), = x.claims
        ids = _held(db, content)
        if not ids:
            return Answer("Unknown", (), ())
        bodies = tuple(_bind(x.body, var, c) for c in ids)
        return dataclasses.replace(x, body=bodies[0], claims=(), alternatives=bodies if len(bodies) > 1 else ())
    found = [(var, _held(db, content)) for var, content in x.claims]
    if x.claims_join == "and":
        if any(not ids for _, ids in found):
            return Answer("Unknown", (), ())
        bodies = [tuple(a for a in x.body)]
        for var, ids in found:
            bodies = [_bind(body, var, c) for body in bodies for c in ids]
        return dataclasses.replace(x, body=bodies[0], claims=(), alternatives=tuple(bodies) if len(bodies) > 1 else ())
    # or: the alternative for each part, bound to each claim held for it
    bodies = [_bind(alt, var, c) for alt, (var, ids) in zip(x.alternatives, found) for c in ids]
    if not bodies:
        return Answer("Unknown", (), ())
    return dataclasses.replace(x, body=bodies[0], claims=(), alternatives=tuple(bodies) if len(bodies) > 1 else ())


def word_claims(db: sqlite3.Connection, a: Answer) -> Answer:
    """A solution that is a claim is shown as what it holds."""
    say_it = lambda v: say.claim_text(db, v) if db.execute("SELECT 1 FROM claim WHERE id = ?", (v,)).fetchone() else v
    return dataclasses.replace(a, solutions=tuple(tuple(say_it(v) for v in s) for s in a.solutions))


def answer_text(db: sqlite3.Connection, a: Answer) -> str:
    proofs = "\n".join(say.proof_text(db, p) for solution in a.proofs for p in solution)
    defeats = defeated(db, [p for solution in a.proofs for p in solution])
    if defeats:
        proofs = (proofs + "\n" if proofs else "") + defeats
    head = say.answer_text(db, word_claims(db, a))
    if a.widened:
        head += "\n(widened: " + "; ".join(a.widened) + ")"
    return f"{head}\n{proofs}" if proofs else head


def extreme_text(db: sqlite3.Connection, a: Answer) -> str:
    """Who is the tallest: the thing, and that it is the tallest among the things compared, not of everything."""
    head, _, proofs = answer_text(db, a).partition("\n")
    if a.value != "Yes":
        return head
    return head + say.AMONG_THOSE + ("\n" + proofs if proofs else "")

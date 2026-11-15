"""Rules the stored facts suggest, as yes-or-no questions. Nothing is stored until one is confirmed."""

import sqlite3
from dataclasses import dataclass

from tolk import say, store


@dataclass(frozen=True)
class Proposal:
    question: str
    p_pred: str
    q_pred: str
    support: tuple[str, ...]  # the things with P, which the rule would also give Q


def propose(db: sqlite3.Connection) -> list[Proposal]:
    """Rules that the stored facts suggest, as yes-or-no questions. Nothing is stored."""
    things: dict[str, set[str]] = {}
    for pred, thing in db.execute(
        "SELECT pred, a0 FROM fact WHERE positive = 1 AND ctx = 'world' AND pred GLOB '_*_n_*' "
        "AND a0 != '' AND a1 = '' AND a2 = ''"
    ):
        things.setdefault(pred, set()).add(thing)
    for pred, thing in db.execute(
        "SELECT pred, a1 FROM fact WHERE positive = 1 AND ctx = 'world' AND pred GLOB '_*_a_*' "
        "AND a1 != '' AND a2 = ''"
    ):
        things.setdefault(pred, set()).add(thing)
    derived = store.derived_pairs(db)
    out = []
    for p, members in sorted(things.items()):
        if len(members) < 3:
            continue
        for q, others in sorted(things.items()):
            if q == p or (p, q) in derived or not members <= others:
                continue
            # Two predicates with one extension are proposed once, in one direction, and not at all once a rule links them either way.
            if members == others and (p > q or (q, p) in derived):
                continue
            out.append(Proposal(say.proposal_text(p, q), p, q, tuple(sorted(members))))
    return out

"""Negation as failure is stratified: which rules may run before which, and which rule sets are refused."""

import sqlite3

from tolk import lf
from tolk.lf import Var


def strata(rules: list[lf.Rule]) -> list[int]:
    """A stratum for each rule: above every rule that can derive an atom it negates, and not below one it reads.
    Raises ValueError for a cycle through negation; check() refuses such a rule before it is stored."""
    level = [0] * len(rules)
    for _ in range(len(rules) + 1):
        moved = False
        for i, r in enumerate(rules):
            for b in r.body:
                for j, s in enumerate(rules):
                    if any(h.pred == b.pred and h.positive for h in s.head):
                        need = level[j] + (0 if b.positive else 1)
                        if level[i] < need:
                            level[i], moved = need, True
        if not moved:
            return level
    raise ValueError("a cycle through negation")


def check(db: sqlite3.Connection, rule: lf.Rule) -> lf.Refusal | None:
    """A rule is stored only if its negated variables are bound by a positive atom and no negated predicate depends on its head."""
    positive_vars = {t for a in rule.body if a.positive for t in a.args if isinstance(t, Var)}
    for a in rule.body:
        if a.positive:
            continue
        for t in a.args:
            if isinstance(t, Var) and not t.event and t not in positive_vars:
                return lf.Refusal("UNSAFE_NEGATION", t.key)
    if not any(a.positive for a in rule.body):
        return lf.Refusal("UNSAFE_NEGATION", "nothing in the body is positive, so the rule would fire on ignorance alone")
    rules = [lf.decode_rule(text) for (text,) in db.execute("SELECT lf FROM rule")] + [rule]
    try:
        strata(rules)
    except ValueError:
        for r in rules:
            for a in r.body:
                if not a.positive and _reaches(rules, a.pred, {h.pred for h in r.head}):
                    return lf.Refusal("NEGATION_CYCLE", a.pred)
        return lf.Refusal("NEGATION_CYCLE", "a cycle through negation")
    return None


def _reaches(rules: list[lf.Rule], start: str, targets: set[str]) -> bool:
    seen, todo = set(), [start]
    while todo:
        pred = todo.pop()
        if pred in targets:
            return True
        if pred in seen:
            continue
        seen.add(pred)
        for r in rules:
            if any(h.pred == pred for h in r.head):
                todo += [b.pred for b in r.body]
    return False

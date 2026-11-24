"""The closed world: what no fact supports is not so. A negated atom holds when no positive fact matches it (negation as failure)."""

import sqlite3

from tolk import lf
from tolk.ask import CONFLICT, NO, NOTHING, UNKNOWN, YES, Answer, _solutions, answer


def close_world(a: Answer, q: lf.Ask) -> Answer:
    """With the world closed, a yes or no question nothing supports is No, and a question for things finds none."""
    if a.value != UNKNOWN:
        return a
    return Answer(NOTHING if q.wanted and q.count is None else NO, (), ())


def answer_closed(db: sqlite3.Connection, q: lf.Ask, ctx: str) -> Answer:
    """The answer with the world closed. A question with a negated atom keeps a candidate for the positive atoms only if no positive fact
    matches the negated ones once the candidate is filled in. A yes or no question that told facts already answer stays as they answer."""
    first = answer(db, q, ctx)
    negated = [a for a in q.body if not a.positive]
    if not negated or q.alternatives or q.count is not None or (not q.wanted and first.value != UNKNOWN):
        return close_world(first, q)
    positive = tuple(a for a in q.body if a.positive)
    shared = sorted({t.key for a in positive for t in a.args if isinstance(t, lf.Var)} & {t.key for a in negated for t in a.args if isinstance(t, lf.Var)})
    wanted = tuple(dict.fromkeys(tuple(q.wanted) + tuple(lf.Var(k) for k in shared)))
    candidates = _solutions(db, lf.Ask(positive, wanted), (1,) * len(positive), ctx) if positive else {(): ()}
    kept = {}
    for values, proofs in candidates.items():
        fill = {v.key: lf.Const(x) for v, x in zip(wanted, values)}
        asked = tuple(lf.Atom(a.pred, tuple(fill.get(t.key, t) if isinstance(t, lf.Var) else t for t in a.args)) for a in negated)
        # The negated atom keeps the tense and modal it was asked with: "Did Kim not sing?" is not answered by "Kim sings.".
        if answer(db, lf.Ask(asked, (), tenses=q.tenses, modals=q.modals), ctx).value != YES:
            kept[values] = proofs
    if not q.wanted:
        return Answer(YES, (), tuple(kept.values())[:1]) if kept else Answer(NO, (), ())
    out = sorted({tuple(v[wanted.index(w)] for w in q.wanted) for v in kept})
    proofs = tuple(next(p for v, p in kept.items() if tuple(v[wanted.index(w)] for w in q.wanted) == o) for o in out)
    return Answer(YES, tuple(out), proofs) if out else Answer(NOTHING, (), ())

"""What a Mind answers to a sentence that asks: a question, a question about every thing, the extreme, a description."""

from tolk import comparison, defaults, kinds, lf, report
from tolk.ask import Answer, answer
from tolk.closed import answer_closed, close_world


def answer_to(mind, x: lf.LF, head: tuple, result):
    """The Result for a sentence that asks, or None for a statement. `result` is the Result class of the mind."""
    if isinstance(x, lf.Ask):
        x = report.bind_claims(mind.db, x) if x.claims else x
        a = x if isinstance(x, Answer) else (answer_closed if mind.closed_world else answer)(mind.db, x, mind.ctx)
        return result(*head, outcome=report.answer_text(mind.db, a), answer=a)
    if isinstance(x, lf.Every):
        value, by_default = defaults.universal(mind.db, x, mind.policy, mind.ctx)
        a = Answer(value, (), (), by_default=by_default)
        return result(*head, outcome=value + (", by default" if by_default and value != "Unknown" else ""), answer=a)
    if isinstance(x, lf.Extreme):
        a = comparison.extreme(mind.db, mind.ctx, x.pred)
        a = close_world(a, lf.Ask((), ("x",))) if mind.closed_world else a
        return result(*head, outcome=report.extreme_text(mind.db, a), answer=a)
    if isinstance(x, lf.Describe):
        return result(*head, outcome=report.describe(mind.db, mind.ctx, x.entity.id))
    if isinstance(x, lf.DescribeKind):
        return result(*head, outcome=kinds.describe(mind.db, mind.ctx, x.pred))
    return None

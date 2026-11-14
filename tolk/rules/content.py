"""Content predicates: a noun, verb, adjective or preposition, with its arguments in role order."""

from tolk import lf
from tolk.lf import Atom, Const

ROLES = ("ARG0", "ARG1", "ARG2")


def map_ep(ctx, ep) -> tuple | lf.Refusal | None:
    if not ep.pred.startswith("_"):
        return None
    if "/" in ep.pred:
        return lf.Refusal("UNKNOWN_WORD", ep.pred)
    if any(k.startswith("ARG") and k not in ROLES for k in ep.args):
        return lf.Refusal("TOO_MANY_ARGUMENTS", ep.pred)
    values = [ep.args[k] for k in ROLES if k in ep.args]
    if not values:
        return lf.Refusal("ARGUMENT_GAP", ep.pred)
    # An unexpressed argument is an i-variable that nothing else mentions.
    expressed = [not (v.startswith("i") and ctx.usage[v] == 1) for v in values]
    last = max((n for n, e in enumerate(expressed) if e), default=-1)
    if not all(expressed[: last + 1]):
        return lf.Refusal("ARGUMENT_GAP", ep.pred)
    is_event = values[0].startswith("e")
    if is_event and len(values) > 1 and not expressed[1]:
        return lf.Refusal("UNEXPRESSED_SUBJECT", ep.pred)
    terms = [ctx.term(v) for v in values[: last + 1]]
    positive = ep.label not in ctx.negated
    if is_event and not positive:
        terms[0] = ctx.no_event(ep)
    return (Atom(ep.pred, tuple(terms), positive),)

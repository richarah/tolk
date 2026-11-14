"""Prepositions that modify an event attach to that event. Their event argument is not used."""

from tolk import lf
from tolk.lf import Atom

# A where-question asks about any locative preposition, so it matches on the sense suffix.
ANY_LOCATIVE = "_*_p_loc"


def map_ep(ctx, ep) -> tuple | lf.Refusal | None:
    if ep.pred == "loc_nonsp":
        if ctx.mode == "tell":
            return lf.Refusal("UNSUPPORTED_PREDICATE", ep.pred)
        return (Atom(ANY_LOCATIVE, (ctx.term(ep.args["ARG1"]), ctx.term(ep.args["ARG2"]))),)
    parts = ep.pred.lstrip("_").split("_")
    if not ep.pred.startswith("_") or len(parts) < 2 or parts[1] != "p":
        return None
    event, obj = ep.args.get("ARG1", ""), ep.args.get("ARG2", "")
    if not event.startswith("e"):
        return lf.Refusal("PREP_NOT_ON_EVENT", ep.pred)
    if not obj or (obj.startswith("i") and ctx.usage[obj] == 1):
        return lf.Refusal("UNEXPRESSED_OBJECT", ep.pred)
    return (Atom(ep.pred, (ctx.term(event), ctx.term(obj)), ep.label not in ctx.negated),)

"""Prepositions that modify an event attach to that event. Their event argument is not used."""

import re
from collections import Counter
from typing import TYPE_CHECKING

from tolk import lf
from tolk.lf import Atom
from tolk.sem import EP

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

# A where-question asks about any locative preposition, so it matches on the sense suffix.
ANY_LOCATIVE = "_*_p_[ls]*"

# Durations and open-ended times belong nowhere in the store: it has years and orderings only.
UNTIMED = re.compile(r"_(since|until|till|during)_p(_.*)?")


def modifies(ep: EP, usage: Counter) -> bool:
    """A modifier event used nowhere else means the modifier is an atom on the event it modifies."""
    return (ep.pred.startswith("_") and ep.args.get("ARG1", "").startswith("e") and ep.args.get("ARG0", "").startswith("e")
            and usage[ep.args["ARG0"]] == 1)


def attached_arity(ep: EP) -> int:
    return 1 + ("ARG2" in ep.args)


def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    if UNTIMED.fullmatch(ep.pred):
        return lf.Refusal("UNSUPPORTED_PREDICATE", ep.pred)
    if ep.pred == "loc_nonsp":
        if ctx.mode == "tell":
            return lf.Refusal("UNSUPPORTED_PREDICATE", ep.pred)
        # "Where does Kim live?" modifies an event; "Where is Bob?" has no verb of its own, so the location's event is the atom's first term.
        lead = () if ep.args["ARG1"].startswith("e") else (ctx.term(ep.args["ARG0"]),)
        return (Atom(ANY_LOCATIVE, (*lead, ctx.term(ep.args["ARG1"]), ctx.term(ep.args["ARG2"]))),)
    if not modifies(ep, ctx.usage):
        return None
    event = ep.args["ARG1"]
    rest = [ep.args[k] for k in ("ARG2",) if k in ep.args]
    if any(v.startswith("i") and ctx.usage[v] == 1 for v in rest):
        return lf.Refusal("UNEXPRESSED_OBJECT", ep.pred)
    return (Atom(ep.pred, (ctx.term(event), *(ctx.term(v) for v in rest)), ep.label not in ctx.negated),)

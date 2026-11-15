"""Comparatives. "A is taller than B" is one fact, comp:<adjective predicate>(A, B), with no event: storing the plain adjective as well
would make "Is A tall?" true. The grammar writes it as the adjective with an event, and more_comp(e, that event, B). "As tall as", "less
tall than" and measures are refused; "Who is the tallest?" is the logical form Extreme."""

import re
from typing import TYPE_CHECKING

from tolk import lf
from tolk.lf import Atom
from tolk.sem import EP, Reading

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

PREFIX = "comp:"
MORE = "more_comp"
SUPERLATIVE = "superl"
ADJECTIVE = re.compile(r"_[^_]+_a(_.*)?")
# Part of speech x is how the grammar writes a word that links clauses or compares ("less ... than"); conditionals and orderings are
# taken by their own families first, and no atom can hold what is left.
POS_X = re.compile(r"_[^_]+_x(_.*)?")


def plan(r: Reading) -> dict[str, EP] | lf.Refusal:
    """The adjective event of each comparison to its more_comp. A comparison must be of a plain adjective, in the present."""
    found: dict[str, EP] = {}
    for more in (ep for ep in r.eps if ep.pred == MORE):
        event = more.args.get("ARG1", "")
        adjective = next((ep for ep in r.eps if ep.args.get("ARG0") == event and ADJECTIVE.fullmatch(ep.pred)), None)
        if adjective is None or not more.args.get("ARG2", "").startswith("x"):
            return lf.Refusal("UNSUPPORTED_PREDICATE", MORE)
        if any(m.pred == "measure" and m.args.get("ARG1") == more.args.get("ARG0") for m in r.eps):
            return lf.Refusal("UNSUPPORTED_PREDICATE", "measure")
        if r.props.get(event, {}).get("TENSE") not in (None, "pres"):
            return lf.Refusal("UNSUPPORTED_TENSE", f"{r.props[event]['TENSE']} on {adjective.pred}")
        found[event] = more
    return found


def superlative(r: Reading) -> str | None:
    """The adjective of a superlative, if that is all the sentence is about besides who it asks for."""
    for ep in r.eps:
        if ep.pred == SUPERLATIVE:
            adjective = next((a for a in r.eps if a.args.get("ARG0") == ep.args.get("ARG1") and ADJECTIVE.fullmatch(a.pred)), None)
            lexical = [a for a in r.eps if a.pred.startswith("_") and "RSTR" not in a.args]
            if adjective is not None and len(lexical) == 2:  # the adjective and the copula
                return adjective.pred
    return None


def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    if ep.pred == SUPERLATIVE:
        return lf.Refusal("UNSUPPORTED_PREDICATE", ep.pred)
    if POS_X.fullmatch(ep.pred):
        return lf.Refusal("UNSUPPORTED_PREDICATE", ep.pred)
    if ep.pred == MORE:
        return ()  # plan checked it has an adjective; that adjective's atom carries both sides
    more = ctx.compared.get(ep.args.get("ARG0", ""))
    if more is None or not ADJECTIVE.fullmatch(ep.pred):
        return None
    other = more.args["ARG2"]
    if other not in ctx.const:
        return lf.Refusal("UNSUPPORTED_PREDICATE", "a comparison with something that is not named: " + ep.pred)
    return (Atom(PREFIX + ep.pred, (ctx.term(ep.args["ARG1"]), ctx.term(other)), ep.label not in ctx.negated),)

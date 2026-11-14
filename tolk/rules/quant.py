"""Quantifiers bind a variable and give no atom. Compile walks their restrictions."""

from tolk import lf

UNIVERSAL = ("_every_q", "udef_q", "_no_q")
INDEF = "_a_q"
DEFINITE = "_the_q"
WH = ("which_q", "_which_q")
QUANTS = (*UNIVERSAL, INDEF, DEFINITE, "proper_q", *WH)


def is_quantifier(ep) -> bool:
    return "RSTR" in ep.args


def map_ep(ctx, ep) -> tuple | lf.Refusal | None:
    if is_quantifier(ep):
        return () if ep.pred in QUANTS else lf.Refusal("UNSUPPORTED_QUANTIFIER", ep.pred)
    # An abstract restriction on a wh word constrains nothing the store can check, so it is not an atom.
    if not ep.pred.startswith("_") and ctx.bound.get(ep.args.get("ARG0")) in WH:
        return ()
    return None

"""Quantifiers bind a variable and give no atom. Compile walks their restrictions."""

import re
from typing import TYPE_CHECKING

from tolk import lf
from tolk.sem import EP

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

UNIVERSAL = ("_every_q", "_all_q", "_each_q", "udef_q", "_no_q")
# A bare plural states a default; these state a rule with no exceptions.
STRICT_UNIVERSAL = ("_every_q", "_all_q", "_each_q", "_no_q")
INDEF = "_a_q"
DEFINITE = "_the_q"
WH = ("which_q", "_which_q")
QUANTS = (*UNIVERSAL, INDEF, DEFINITE, "proper_q", "pronoun_q", *WH)

# A demonstrative (this, that, these, those) needs something pointed at, which a sentence by itself does not give. The grammar
# also offers it as a reading of a complementiser, so such a reading is passed over; it is not a meaning the store cannot hold.
DEMONSTRATIVE = re.compile(r"_[^_]+_q_dem")


def is_quantifier(ep: EP) -> bool:
    return "RSTR" in ep.args

def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    if is_quantifier(ep):
        return () if ep.pred in QUANTS else lf.Refusal("UNSUPPORTED_QUANTIFIER", ep.pred)
    # An abstract restriction on a wh word constrains nothing the store can check, so it is not an atom.
    if not ep.pred.startswith("_") and ctx.bound.get(ep.args.get("ARG0")) in WH:
        return ()
    return None

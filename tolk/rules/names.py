"""Names: a named predication gives its variable a constant, and two names in a compound are one constant."""

from typing import TYPE_CHECKING

from tolk import lf
from tolk.sem import EP, Reading

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

def plan(r: Reading) -> dict[str, str]:
    consts = {ep.args["ARG0"]: ep.args["CARG"].lower() for ep in r.eps if ep.pred == "named"}
    for ep in r.eps:
        if ep.pred == "compound":
            head, modifier = ep.args["ARG1"], ep.args["ARG2"]
            if head in consts and modifier in consts:
                # The head comes last in the text, so the modifier's name leads.
                joined = f"{consts[modifier]}_{consts[head]}"
                consts[head] = consts[modifier] = joined
    return consts

def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    if ep.pred in ("named", "compound"):
        return ()
    return None

"""Cardinals and How many. A cardinal on a thing says how many distinct things; digits and number words give the same predication."""

from typing import TYPE_CHECKING

from tolk import lf
from tolk.sem import EP, Reading

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

# The grammar's degree machinery for "how many": the counted noun is the argument of the many-word.
DEGREE_PREDS = ("abstr_deg", "measure", "much-many_a")


def cardinals(r: Reading) -> dict[str, int] | lf.Refusal:
    out: dict[str, int] = {}
    for ep in r.eps:
        if ep.pred == "card":
            if not ep.args["CARG"].isdigit() or int(ep.args["CARG"]) < 1:
                return lf.Refusal("UNSUPPORTED_PREDICATE", f"card {ep.args['CARG']}")
            out[ep.args["ARG1"]] = int(ep.args["CARG"])
    return out


def how_many(r: Reading) -> tuple[str, str] | None:
    """(the counted variable, the degree variable) if the sentence asks how many."""
    for ep in r.eps:
        if ep.pred == "much-many_a":
            counted = ep.args["ARG1"]
            for m in r.eps:
                if m.pred == "measure" and m.args.get("ARG1") == ep.args["ARG0"]:
                    return counted, m.args["ARG2"]
    return None


def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    if ep.pred == "card" or ep.pred in DEGREE_PREDS:
        return ()
    return None

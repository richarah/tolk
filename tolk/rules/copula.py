"""The identity copula. An indefinite complement describes the subject, so it adds atoms to the subject and creates nothing."""

from typing import TYPE_CHECKING

from tolk import lf
from tolk.sem import EP
from tolk.rules import quant

if TYPE_CHECKING:
    from tolk.compile import Ctx

def is_copula(ep: EP) -> bool:
    return ep.pred.endswith("_v_id")

def plan(eps: list[EP] | tuple[EP, ...], bound: dict[str, str]) -> dict[str, str]:
    alias = {}
    for ep in eps:
        if is_copula(ep) and bound.get(ep.args["ARG2"]) in (quant.INDEF, *quant.UNIVERSAL):
            alias[ep.args["ARG2"]] = ep.args["ARG1"]
    return alias

def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    if not is_copula(ep):
        return None
    if ep.args["ARG2"] in ctx.const:
        # Two names make an identity, which compile returns as Same before mapping. A named complement
        # with a non-name subject is not stored.
        return lf.Refusal("IDENTITY_NOT_YET", ep.pred)
    return ()

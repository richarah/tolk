"""The identity copula: an indefinite complement describes the subject, so it adds atoms to the subject and creates nothing."""

from tolk import lf
from tolk.rules import quant


def is_copula(ep) -> bool:
    return ep.pred.endswith("_v_id")


def plan(eps, bound: dict[str, str]) -> dict[str, str]:
    alias = {}
    for ep in eps:
        if is_copula(ep) and bound.get(ep.args["ARG2"]) in (quant.INDEF, *quant.UNIVERSAL):
            alias[ep.args["ARG2"]] = ep.args["ARG1"]
    return alias


def map_ep(ctx, ep) -> tuple | lf.Refusal | None:
    if not is_copula(ep):
        return None
    if ep.args["ARG2"] in ctx.const:
        return lf.Refusal("IDENTITY_NOT_YET", ep.pred)
    return ()

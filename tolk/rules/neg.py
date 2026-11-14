"""Negation: a neg predication negates the clause its handle points to. Compile marks those clauses."""

from typing import TYPE_CHECKING

from tolk import lf
from tolk.sem import EP, Reading

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

def labels(r: Reading) -> set[str]:
    return {r.qeq.get(ep.args["ARG1"], ep.args["ARG1"]) for ep in r.eps if ep.pred == "neg"}

def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    return () if ep.pred == "neg" else None

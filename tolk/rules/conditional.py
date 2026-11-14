"""A conditional: the grammar's if-then predication holds the consequent and the antecedent as two clauses."""

import re
from typing import TYPE_CHECKING

from tolk import lf
from tolk.sem import EP, Reading

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

# Part of speech x: a function word that relates two clauses. Its first clause is the consequent, its second the antecedent.
CONDITIONAL = re.compile(r"_[^_]+_x_[^_]+")


def find(r: Reading, main: list[EP]) -> EP | None:
    for ep in main:
        if CONDITIONAL.fullmatch(ep.pred) and ep.args.get("ARG1", "").startswith("h") and ep.args.get("ARG2", "").startswith("h"):
            return ep
    return None


def labels(r: Reading, ep: EP) -> tuple[str, str]:
    """(antecedent label, consequent label)."""
    return r.qeq[ep.args["ARG2"]], r.qeq[ep.args["ARG1"]]


def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    return () if CONDITIONAL.fullmatch(ep.pred) and ep.args.get("ARG1", "").startswith("h") else None

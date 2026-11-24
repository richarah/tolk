"""Negation: a neg predication negates the clause its handle points to. Compile marks those clauses."""

from typing import TYPE_CHECKING

from tolk import lf
from tolk.rules import modal
from tolk.sem import EP, Reading

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

def labels(r: Reading) -> set[str]:
    """The labels a neg negates. A modal under the negation ("cannot") passes it on to the clause the modal modifies: the negative fact
    is about that clause's event, which carries the modal."""
    frontier = [r.qeq.get(ep.args["ARG1"], ep.args["ARG1"]) for ep in r.eps if ep.pred == "neg"]
    out: set[str] = set()
    while frontier:
        label = frontier.pop()
        if label in out:
            continue
        out.add(label)
        frontier += [r.qeq.get(ep.args["ARG1"], ep.args["ARG1"]) for ep in r.eps
                     if ep.label == label and modal.MODAL.fullmatch(ep.pred) and "ARG1" in ep.args]
    return out

def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    return () if ep.pred == "neg" else None

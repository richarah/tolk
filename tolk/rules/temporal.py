"""Before and after between two clauses: an ordering between their events. A year on an event is an ordinary modifier."""

import re
from typing import TYPE_CHECKING

from tolk import lf
from tolk.lf import Atom
from tolk.sem import EP, Reading

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

TEMPORAL = re.compile(r"_(before|after)_x_h")


def find(r: Reading) -> list[EP]:
    return [ep for ep in r.eps if TEMPORAL.fullmatch(ep.pred)]


def order(ctx: "Ctx", r: Reading) -> tuple[Atom, ...] | lf.Refusal:
    """before(first, second) for each temporal predication. The first clause is the main clause, the second the subordinate one;
    after is stored as before the other way round, so the store has one relation."""
    out = []
    for ep in find(r):
        events = []
        for hole in (ep.args["ARG1"], ep.args["ARG2"]):
            label = r.qeq.get(hole)
            clause = [e for e in r.eps if e.label == label and e.pred.startswith("_") and e.args.get("ARG0", "").startswith("e")]
            if not clause:
                return lf.Refusal("UNSUPPORTED_PREDICATE", ep.pred)
            events.append(ctx.term(clause[0].args["ARG0"]))
        first, second = events if TEMPORAL.fullmatch(ep.pred).group(1) == "before" else events[::-1]
        out.append(Atom(lf.BEFORE, (first, second)))
    return tuple(out)


def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    return () if TEMPORAL.fullmatch(ep.pred) else None

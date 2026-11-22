"""Modals: can, must, might, should, may, could, would. Each is stored on the event it modifies, as modal(event, kind); a question asks
about each event for the modal it has, or for none. A modal in a rule, or with a negation, is refused."""

import re

from tolk import lf
from tolk.lf import Atom, Const, Var
from tolk.sem import EP, Reading

MODAL = re.compile(r"_(can|must|might|should|may|could|would)_v_modal")


def find(r: Reading) -> list[EP]:
    return [ep for ep in r.eps if MODAL.fullmatch(ep.pred)]


def kind(ep: EP) -> str:
    return MODAL.fullmatch(ep.pred).group(1)


def targets(ctx, r: Reading, ep: EP) -> list:
    """The verb events the modal modifies: the events on the label its handle resolves to."""
    label = r.qeq.get(ep.args.get("ARG1"), ep.args.get("ARG1"))
    return [ctx.term(v.args["ARG0"]) for v in r.eps
            if v.label == label and v.pred.startswith("_") and v.args.get("ARG0", "").startswith("e")]


def atoms(ctx, r: Reading, used: tuple) -> tuple[Atom, ...]:
    """modal(event, kind) for each modified event that the atoms of the statement mention."""
    out = []
    for ep in find(r):
        for t in targets(ctx, r, ep):
            if t in used:
                out.append(Atom(lf.MODAL, (t, Const(kind(ep), "value"))))
    return tuple(out)


def asked(ctx, r: Reading, body: tuple[Atom, ...]) -> tuple[tuple[Var, str], ...]:
    """Per event of the question, the kind of modal it asks for, or "" for a question with none."""
    by_event = {t: kind(ep) for ep in find(r) for t in targets(ctx, r, ep)}
    events = []
    for a in body:
        if a.args and isinstance(a.args[0], Var) and a.args[0].event and a.args[0] not in events:
            events.append(a.args[0])
    return tuple((t, by_event.get(t, "")) for t in events)

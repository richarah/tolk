"""Modals: can, must, might, should, may, could, would. Each is stored on the event it modifies, as modal(event, kind); a question asks
about each event for the modal it has, or for none. A modal in a rule is refused. A negated modal ("cannot", "must not") is a negative
fact whose event carries the modal, so it contradicts the same modal only: "Kim cannot sing." against "Kim can sing."."""

import re

from tolk import lf
from tolk.lf import Atom, Const, Var
from tolk.sem import EP, Reading

MODAL = re.compile(r"_(can|must|might|should|may|could|would)_v_modal")


def find(r: Reading) -> list[EP]:
    return [ep for ep in r.eps if MODAL.fullmatch(ep.pred)]


# A modal in the past is the word that says it: the grammar reads "could" as can in the past as well as could itself, and both are "could".
PAST = {"can": "could"}


def kind(ep: EP, r: Reading | None = None) -> str:
    word = MODAL.fullmatch(ep.pred).group(1)
    if r is not None and r.props.get(ep.args.get("ARG0", ""), {}).get("TENSE") == "past":
        return PAST.get(word, word)
    return word


def targets(ctx, r: Reading, ep: EP) -> list:
    """The verb events the modal modifies: the events on the label its handle resolves to. A negation between the modal and the verb
    ("must not sing") is passed through: the negated verb's event carries the modal."""
    labels, frontier = set(), [r.qeq.get(ep.args.get("ARG1"), ep.args.get("ARG1"))]
    while frontier:
        label = frontier.pop()
        if label in labels:
            continue
        labels.add(label)
        frontier += [r.qeq.get(n.args["ARG1"], n.args["ARG1"]) for n in r.eps if n.label == label and n.pred == "neg" and "ARG1" in n.args]
    return [ctx.term(v.args["ARG0"]) for v in r.eps
            if v.label in labels and v.pred.startswith("_") and v.args.get("ARG0", "").startswith("e")]


def progressive(ctx, r: Reading) -> list:
    """The verb events in the progressive (the aspect is PROG on the event): kind "prog" is stored on them, as a modal is."""
    return [ctx.term(v.args["ARG0"]) for v in r.eps
            if v.pred.startswith("_") and v.args.get("ARG0", "").startswith("e") and r.props.get(v.args["ARG0"], {}).get("PROG") == "+"]


def atoms(ctx, r: Reading, used: tuple) -> tuple[Atom, ...]:
    """modal(event, kind) for each modified event that the atoms of the statement mention, and modal(event, prog) for each progressive."""
    out = []
    for ep in find(r):
        for t in targets(ctx, r, ep):
            if t in used:
                out.append(Atom(lf.MODAL, (t, Const(kind(ep, r), "value"))))
    for t in progressive(ctx, r):
        if t in used:
            out.append(Atom(lf.MODAL, (t, Const("prog", "value"))))
    return tuple(out)


def asked(ctx, r: Reading, body: tuple[Atom, ...]) -> tuple[tuple[Var, str], ...]:
    """Per event of the question, the kind of modal it asks for, or "" for a question with none."""
    by_event = {t: kind(ep, r) for ep in find(r) for t in targets(ctx, r, ep)}
    by_event.update({t: "prog" for t in progressive(ctx, r)})
    events = []
    for a in body:
        if a.args and isinstance(a.args[0], Var) and a.args[0].event and a.args[0] not in events:
            events.append(a.args[0])
    return tuple((t, by_event.get(t, "")) for t in events)

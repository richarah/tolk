"""Negation: a neg predication negates the clause its handle points to. Compile marks those clauses."""

from tolk import lf


def labels(r) -> set[str]:
    return {r.qeq.get(ep.args["ARG1"], ep.args["ARG1"]) for ep in r.eps if ep.pred == "neg"}


def map_ep(ctx, ep) -> tuple | lf.Refusal | None:
    return () if ep.pred == "neg" else None

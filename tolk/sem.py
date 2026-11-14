from dataclasses import dataclass

from delphin.codecs import simplemrs


@dataclass(frozen=True)
class EP:
    pred: str
    label: str
    args: dict[str, str]
    cfrom: int = -1  # character span in the sentence; -1 when the parser gave none
    cto: int = -1


@dataclass(frozen=True)
class Reading:
    top: str
    index: str
    eps: tuple[EP, ...]
    qeq: dict[str, str]
    props: dict[str, dict[str, str]]


def read(simplemrs_text: str) -> Reading:
    m = simplemrs.decode(simplemrs_text)
    eps = []
    for ep in m.rels:
        args = {k: v for k, v in ep.args.items()}
        if ep.carg is not None:
            args["CARG"] = ep.carg
        eps.append(EP(ep.predicate, ep.label, args, ep.cfrom, ep.cto))
    qeq = {hc.hi: hc.lo for hc in m.hcons}
    props = {v: dict(p) for v, p in m.variables.items()}
    return Reading(m.top, m.index, tuple(eps), qeq, props)


def to_dict(r: Reading) -> dict:
    return {
        "top": r.top,
        "index": r.index,
        "eps": [{"pred": e.pred, "label": e.label, "args": e.args} for e in r.eps],
        "qeq": r.qeq,
        "props": r.props,
    }

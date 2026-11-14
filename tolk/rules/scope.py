"""Which predications belong to the main clause, to a restriction, to a negated clause, and what a definite refers to."""

from tolk import lf
from tolk.rules import copula, neg
from tolk.rules.ctx import Lookup
from tolk.sem import EP, Reading


def main_labels(r: Reading, start: str | None = None) -> set[str]:
    """The top clause, or the clause with label start, and any clause a neg at its top points at."""
    labels = {start or r.qeq[r.top]}
    grew = True
    while grew:
        more = {r.qeq.get(ep.args["ARG1"], ep.args["ARG1"]) for ep in r.eps if ep.pred == "neg" and ep.label in labels}
        grew = not more <= labels
        labels |= more
    return labels


def negated(r: Reading, quants: list[EP], alias: dict[str, str], bound: dict[str, str]) -> set[str]:
    """Labels of the clauses a neg predication negates, widened to a copula complement's restriction."""
    negated = neg.labels(r)
    for ep in r.eps:
        if copula.is_copula(ep) and ep.label in negated and ep.args["ARG2"] in alias:
            for q in quants:
                if q.args["ARG0"] == ep.args["ARG2"]:
                    negated.add(r.qeq.get(q.args["RSTR"]))
    return negated


def definite(r: Reading, q: EP, lookup: Lookup | None) -> str | lf.Refusal:
    if lookup is None:
        return lf.Refusal("DEFINITE_NEEDS_STORE", q.pred)
    var = q.args["ARG0"]
    target = r.qeq.get(q.args["RSTR"])
    restr = [ep for ep in r.eps if ep.label == target and ep.args.get("ARG0") == var]
    cands = set.intersection(*(lookup(ep.pred) for ep in restr)) if restr else set()
    if len(cands) != 1:
        return lf.Refusal("DEFINITE_MATCHES", f"{len(cands)} known things match")
    return next(iter(cands))


def restricted(r: Reading, quants: list[EP], universal_top: list[EP]) -> set[int]:
    """Indices of predications inside a universal's restriction, including nested indefinites' restrictions."""
    body: set[int] = set()
    for q in universal_top:
        body |= expand(r, quants, _restriction(r, q))
    return body


def clause(r: Reading, quants: list[EP], label: str) -> set[int]:
    """Indices of the predications of a clause and of the restrictions of the quantifiers over its variables."""
    labels = main_labels(r, label)
    return expand(r, quants, [i for i, ep in enumerate(r.eps) if ep.label in labels])


def _restriction(r: Reading, q: EP) -> list[int]:
    target = r.qeq.get(q.args["RSTR"])
    return [i for i, ep in enumerate(r.eps) if ep.label == target]


def expand(r: Reading, quants: list[EP], frontier: list[int]) -> set[int]:
    found: set[int] = set()
    while frontier:
        i = frontier.pop()
        if i in found:
            continue
        found.add(i)
        for q in quants:
            if q.args["ARG0"] in r.eps[i].args.values():
                frontier += _restriction(r, q)
    return found

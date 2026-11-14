"""Who is X? and What is X?: the copula between a known thing and a wh word that has no restriction."""

from tolk.rules import copula, quant
from tolk.sem import EP, Reading


def entity(r: Reading, main: list[EP], bound: dict[str, str], const: dict[str, str]) -> str | None:
    """The id of the thing being described, or None if the question is not of this shape."""
    for ep in main:
        if not copula.is_copula(ep):
            continue
        for known, asked in ((ep.args["ARG1"], ep.args["ARG2"]), (ep.args["ARG2"], ep.args["ARG1"])):
            if known in const and bound.get(asked) in quant.WH and _unrestricted(r, asked):
                return const[known]
    return None


def _unrestricted(r: Reading, var: str) -> bool:
    # The restriction the grammar gives a wh word is an abstract predicate; a lexical noun would narrow the question and give an atom.
    return all(not ep.pred.startswith("_") for ep in r.eps if ep.args.get("ARG0") == var and not quant.is_quantifier(ep))

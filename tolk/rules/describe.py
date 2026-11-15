"""Who is X? and What is X?: the copula between a known thing and a wh word that has no restriction."""

from tolk import lf
from tolk.rules import content, copula, quant
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


def kind(r: Reading, main: list[EP]) -> str | lf.Refusal | None:
    """The predicate of the noun being asked about: the copula between a wh word with no restriction and a noun that has no determiner
    but an indefinite or a bare plural, as in What is a fish? What is fish? What are birds?"""
    for ep in main:
        if not copula.is_copula(ep):
            continue
        for known, asked in ((ep.args["ARG1"], ep.args["ARG2"]), (ep.args["ARG2"], ep.args["ARG1"])):
            nouns = [n for n in r.eps if n.args.get("ARG0") == known and n.pred.startswith("_") and "RSTR" not in n.args]
            quants = [q.pred for q in r.eps if quant.is_quantifier(q) and q.args["ARG0"] == known]
            wh = any(q.pred in quant.WH and q.args["ARG0"] == asked for q in r.eps) and any(
                t.pred == "thing" and t.args["ARG0"] == asked for t in r.eps)  # What, not Who: Who is a bird? asks for the birds
            if wh and _unrestricted(r, asked) and len(nouns) == 1 and quants and quants[0] in (quant.INDEF, "udef_q"):
                return content.known_as(nouns[0].pred) if "/" in nouns[0].pred else nouns[0].pred
    return None

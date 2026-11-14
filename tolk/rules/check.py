"""Checks that a compiled reading dropped nothing."""

from tolk import lf
from tolk.lf import Atom, Var
from tolk.rules.ctx import Ctx
from tolk.sem import EP, Reading


def tense(r: Reading) -> lf.Refusal | None:
    """Only present, and past on the main event, are stored. Anything else would be dropped without a trace."""
    for ep in r.eps:
        v = ep.args.get("ARG0", "")
        if not (ep.pred.startswith("_") and v.startswith("e")):
            continue
        p = r.props.get(v, {})
        if p.get("PERF") == "+" or p.get("PROG") == "+":
            return lf.Refusal("UNSUPPORTED_ASPECT", ep.pred)
        if p.get("TENSE") not in (None, "untensed", "pres") and not (v == r.index and p["TENSE"] == "past"):
            return lf.Refusal("UNSUPPORTED_TENSE", f"{p['TENSE']} on {ep.pred}")
    return None


def unconsumed(ctx: Ctx, quants: list[EP], out: lf.LF, mode: str) -> lf.Refusal | None:
    """A reading compiles only if nothing in it was silently dropped."""
    atoms = atoms_of(out)
    terms = {t for a in atoms for t in a.args}
    if mode == "ask":
        if any(not a.positive for a in atoms):
            return lf.Refusal("NEGATED_QUESTION", "absence of a fact cannot answer a negated question")
        positive = {t for a in atoms if a.positive for t in a.args}
        loose = [v.key for v in out.wanted if v not in positive]
        if loose:
            return lf.Refusal("UNCONSTRAINED_WANTED", ", ".join(loose) + " is wanted but no positive atom mentions it")
        if not atoms:
            return lf.Refusal("UNCONSUMED", "a question with no atom")
    if ctx.negated and all(a.positive for a in atoms):
        return lf.Refusal("UNCONSUMED", "a negation that negates no atom")
    dropped = [q.args["ARG0"] for q in quants if ctx.term(q.args["ARG0"]) not in terms]
    if dropped:
        return lf.Refusal("UNCONSUMED", "no atom uses " + ", ".join(dropped))
    return None


def unbound(x: lf.LF, bound: dict[str, str]) -> str:
    """Names of variables that no quantifier binds and that are not events. Such a variable would be silently ignored."""
    keys = {t.key for a in atoms_of(x) for t in a.args if isinstance(t, Var)}
    names_ = sorted(k for k in keys if not Var(k).event and k not in bound)
    return ", ".join(names_)


def atoms_of(x: lf.LF) -> list[Atom]:
    if isinstance(x, lf.Tell):
        return list(x.atoms)
    if isinstance(x, lf.Rule):
        return list(x.head + x.body)
    if isinstance(x, lf.Ask):
        return list(x.body)
    return []

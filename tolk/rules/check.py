"""Checks that a compiled reading dropped nothing."""

from tolk import lf
from tolk.lf import Atom, Var
from tolk.rules import coordination, temporal
from tolk.rules.modal import MODAL
from tolk.rules.ctx import Ctx
from tolk.sem import EP, Reading


def tense(r: Reading) -> lf.Refusal | None:
    """Past, future, and present perfect are stored on the main event (or a clause of an and or or): tense(e, past) or tense(e, fut).
    A present perfect is stored as a past event. Anything else would be dropped without a trace, so it is refused."""
    ordered = bool(temporal.find(r))
    # The clauses joined by and or or are main events too: each is stored with its own tense.
    clauses = {ep.args[k] for ep in r.eps if coordination.CONJUNCTION.fullmatch(ep.pred) for k in ("ARG1", "ARG2") if k in ep.args}
    for ep in r.eps:
        v = ep.args.get("ARG0", "")
        if not (ep.pred.startswith("_") and v.startswith("e")) or MODAL.fullmatch(ep.pred):
            continue  # a modal's own predication carries a tense of its own; the event it modifies is checked
        p = r.props.get(v, {})
        main = v == r.index or ordered or v in clauses
        if p.get("PROG") == "+":
            return lf.Refusal("UNSUPPORTED_ASPECT", ep.pred)
        if p.get("PERF") == "+":
            if p.get("TENSE") != "pres" or not main:
                return lf.Refusal("UNSUPPORTED_ASPECT", ep.pred)  # past perfect, future perfect, or a perfect that is not a main event
            continue
        tense_value = p.get("TENSE")
        if tense_value in (None, "untensed", "pres"):
            continue
        if tense_value in ("past", "fut") and main:
            continue
        return lf.Refusal("UNSUPPORTED_TENSE", f"{tense_value} on {ep.pred}")
    return None


def unconsumed(ctx: Ctx, quants: list[EP], out: lf.LF, mode: str) -> lf.Refusal | None:
    """A reading compiles only if nothing in it was silently dropped."""
    atoms = atoms_of(out)
    terms = {t for a in atoms for t in a.args}
    if mode == "ask":
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
    keys -= {ref.key for ref, _ in getattr(x, "claims", ()) if isinstance(ref, Var)}  # a claim asked about is bound by its content
    names_ = sorted(k for k in keys if not Var(k).event and k not in bound)
    return ", ".join(names_)


def atoms_of(x: lf.LF) -> list[Atom]:
    if isinstance(x, lf.Tell):
        return list(x.atoms) + [a for _, atoms in x.claims for a in atoms]
    if isinstance(x, (lf.Rule, lf.Every)):
        return list(x.head + x.body)
    if isinstance(x, lf.Ask):
        return list(x.body) + [a for _, atoms in x.claims for a in atoms]
    return []

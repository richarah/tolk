"""Claims: a verb whose object is a clause with a tense that belongs to it (a report of belief or speech), or a control verb, is a claim.
The clause holds in a context apart from the world, and the world holds only that someone has the claim. Which verb it is is not asked."""

from typing import TYPE_CHECKING

from tolk import lf
from tolk.sem import EP, Reading

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx


def find(r: Reading) -> list[tuple[EP, str]]:
    """(the verb, the label of its clause) for each verb whose second argument is a clause with a present or past event: a report of
    belief or speech. A control verb with an infinitive is a claim of the verb's subject, whoever the infinitive's subject is: "Kim wants to
    sing." is a claim Kim has, that Kim sings; "Lee wants Kim to sing." is a claim Lee has, about Kim's singing."""
    out = []
    for ep in r.eps:
        hole = ep.args.get("ARG2", "")
        if ep.pred.startswith("_") and hole.startswith("h") and not ep.args.get("ARG1", "h").startswith("h"):
            label = r.qeq.get(hole)
            if any(e.label == label and e.args.get("ARG0", "").startswith("e") and r.props.get(e.args["ARG0"], {}).get("TENSE") in ("pres", "past")
                   for e in r.eps) or any(
                    e.label == label and e.args.get("ARG0", "").startswith("e") and r.props.get(e.args["ARG0"], {}).get("TENSE") == "untensed"
                    for e in r.eps):
                out.append((ep, label))
    return out


def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    """The verb becomes an atom whose last argument is the claim."""
    term = ctx.claim.get(ep.args.get("ARG2", ""))
    if term is None:
        return None
    return (lf.Atom(ep.pred, (ctx.term(ep.args["ARG0"]), ctx.term(ep.args["ARG1"]), term), ep.label not in ctx.negated),)


def claim_key(atoms: tuple["lf.Atom", ...]) -> str:
    """The content of a claim, independent of how its events and things were numbered, so that a told claim and an asked one compare."""
    def render(order: list) -> list[str]:
        table: dict = {}

        def name(t) -> str:
            if isinstance(t, lf.Var) or t.kind in lf.FRESH:
                return table.setdefault(t, f"#{len(table)}")
            return t.id

        return sorted(f"{'' if a.positive else 'not '}{a.pred}({','.join(name(t) for t in a.args)})" for a in order)

    order = sorted(atoms, key=lambda a: (a.pred, len(a.args), tuple(t.id if isinstance(t, lf.Const) and t.kind not in lf.FRESH else "" for t in a.args)))
    return ";".join(render(order))

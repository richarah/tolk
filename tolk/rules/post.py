"""The last steps of compiling a reading: the tenses of its events, the things a cardinal makes, the things it mentions."""

from tolk import lf
from tolk.lf import Atom, Const, Var
from tolk.rules import check, pronouns
from tolk.rules.ctx import Ctx
from tolk.sem import EP, Reading


def tenses(ctx: Ctx, r: Reading, atoms: tuple[Atom, ...]) -> tuple[Atom, ...]:
    """tense(event, past) for each past event that the atoms mention. Present is not stored: it is what an event is by default."""
    used = {t for a in atoms for t in a.args}
    found: list[Atom] = []
    for ep in r.eps:
        v = ep.args.get("ARG0", "")
        if ep.pred.startswith("_") and v.startswith("e") and r.props.get(v, {}).get("TENSE") == "past":
            t = ctx.term(v)
            atom = Atom(lf.TENSE, (t, Const("past", "value")))
            if t in used and atom not in found:
                found.append(atom)
    return tuple(found)


def asked_tenses(ctx: Ctx, r: Reading, out: lf.Ask) -> tuple[tuple[Var, str], ...]:
    """The tense each event of the question must carry: a past question needs a past event, a present one an event that is not past."""
    used = {t for alt in (out.alternatives or (out.body,)) for a in alt for t in a.args}
    found: list[tuple[Var, str]] = []
    for ep in r.eps:
        v = ep.args.get("ARG0", "")
        tense = r.props.get(v, {}).get("TENSE")
        if ep.pred.startswith("_") and v.startswith("e") and tense in ("past", "pres"):
            t = ctx.term(v)
            if isinstance(t, Var) and t in used and (t, tense) not in found:
                found.append((t, tense))
    return tuple(found)


def expand(ctx: Ctx, atoms: tuple[Atom, ...], cards: dict[str, int]) -> tuple[Atom, ...]:
    """A cardinal makes that many distinct things: each atom about the thing is repeated for each of them."""
    for var, n in cards.items():
        t = ctx.term(var)
        if not isinstance(t, Const) or t.kind != "anon":
            continue
        copies = [t]
        for _ in range(n - 1):
            ctx.counts["anon"] += 1
            copies.append(Const(lf.fresh_id("anon", ctx.counts["anon"]), "anon"))
        atoms = tuple(
            b for a in atoms for b in (
                [Atom(a.pred, tuple(c if x == t else x for x in a.args), a.positive) for c in copies] if t in a.args else [a])
        )
    return atoms


def mentions(r: Reading, ctx: Ctx, quants: list[EP], out: lf.LF) -> tuple[tuple[int, str, str], ...]:
    """Things this sentence mentions, by position, for pronouns in later sentences. A thing the sentence creates is marked with ~ and its local id, until the store numbers it."""
    used = {t for a in check.atoms_of(out) for t in a.args}
    found = []
    for q in quants:
        t = ctx.term(q.args["ARG0"])
        if isinstance(t, Const) and t.kind in ("named", "anon") and t.id not in (pronouns.USER, pronouns.TOLK) and (t in used or t.kind == "named"):
            found.append((q.cfrom, ("~" if t.kind == "anon" else "") + t.id, r.props.get(q.args["ARG0"], {}).get("NUM", "sg")))
    return tuple(sorted(found))

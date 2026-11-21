"""And and or. A noun-phrase conjunction is a group variable that the verb takes; it distributes over its members.
A clause or verb-phrase conjunction joins two events that need no further handling. An or is only taken in questions."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tolk import lf
from tolk.lf import Atom, Term, Var
from tolk.sem import EP, Reading

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

CONJUNCTION = re.compile(r"_(and|or)_c")


@dataclass(frozen=True)
class Conj:
    op: str
    group: str  # the group variable, or the event the conjunction is about
    members: tuple[str, str]

    @property
    def nominal(self) -> bool:
        return self.group.startswith("x")


def find(r: Reading) -> list[Conj]:
    return [Conj(m.group(1), ep.args["ARG0"], (ep.args["ARG1"], ep.args["ARG2"]))
            for ep in r.eps if (m := CONJUNCTION.fullmatch(ep.pred))]


def leaves(conjs: list[Conj], var: str) -> list[str] | lf.Refusal:
    """The members of a group, looking through members that are groups; and and or may not be mixed."""
    inner = next((c for c in conjs if c.group == var), None)
    if inner is None:
        return [var]
    out: list[str] = []
    for m in inner.members:
        sub = next((c for c in conjs if c.group == m), None)
        if sub is not None and sub.op != inner.op:
            return lf.Refusal("COORDINATION", "and and or in one list")
        got = leaves(conjs, m)
        if isinstance(got, lf.Refusal):
            return got
        out += got
    return out


def distribute(ctx: "Ctx", atoms: tuple[Atom, ...], conjs: list[Conj]) -> list[tuple[Atom, ...]] | lf.Refusal:
    """Alternatives: one set of atoms, or in a question one set per side of an or."""
    member_of = {m for c in conjs for m in c.members}
    alts = [atoms]
    for c in conjs:
        if c.group in member_of:
            continue
        if c.op == "or" and ctx.mode != "ask":
            return lf.Refusal("COORDINATION", "or in a statement")
        if ctx.mode == "rule" and c.nominal:
            return lf.Refusal("COORDINATION", "a noun-phrase conjunction in a rule")
        sides = leaves(conjs, c.group)
        if isinstance(sides, lf.Refusal):
            return sides
        terms = [ctx.term(s) for s in sides]
        if c.nominal:
            whole = ctx.term(c.group)
            alts = [b for alt in alts for b in _split(alt, whole, terms, c.op)]
        elif c.op == "or":
            alts = [b for alt in alts for b in _split(alt, None, terms, c.op)]
    return alts


def _split(atoms: tuple[Atom, ...], whole: Term | None, terms: list[Term], op: str) -> list[tuple[Atom, ...]]:
    if op == "and":
        # A copy takes a new event when nothing else is said about that event, so the members need not share one.
        elsewhere = {x for a in atoms if whole not in a.args for x in a.args}
        local = {x for a in atoms if whole in a.args for x in a.args if isinstance(x, Var) and x.event and x not in elsewhere}

        def copy(a: Atom, k: int, t: Term) -> Atom:
            return Atom(a.pred, tuple(t if x == whole else Var(f"{x.key}c{k}") if k and x in local else x for x in a.args), a.positive)

        return [tuple(b for a in atoms for b in ([copy(a, k, t) for k, t in enumerate(terms)] if whole in a.args else [a]))]
    out = []
    for i, term in enumerate(terms):
        # An alternative keeps the atoms that are not about another side, and states the group's atoms about that side.
        others = [t for j, t in enumerate(terms) if j != i and isinstance(t, Var)]
        alt = []
        for a in atoms:
            if whole is not None and whole in a.args:
                alt.append(Atom(a.pred, tuple(term if x == whole else x for x in a.args), a.positive))
            elif not any(_about(a, o) for o in others):
                alt.append(a)
        out.append(tuple(alt))
    return out


def _about(a: Atom, side: Var) -> bool:
    """Whether an atom is about a side of an or: its event, or a copy of that event that an and made for one member (e4c1)."""
    return any(isinstance(x, Var) and (x.key == side.key or re.fullmatch(re.escape(side.key) + r"c\d+", x.key)) for x in a.args)


def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    return () if CONJUNCTION.fullmatch(ep.pred) else None

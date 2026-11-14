"""Reading to logical form. Families in tolk/rules each map one predicate; this module decides scope and variable kinds."""

from collections import Counter
from dataclasses import dataclass, field

from tolk import lf
from tolk.lf import Atom, Const, Var
from tolk.rules import content, copula, names, quant
from tolk.sem import EP, Reading

FAMILIES = (names, quant, copula, content)


@dataclass
class Ctx:
    mode: str
    bound: dict[str, str]
    alias: dict[str, str]
    const: dict[str, str]
    usage: Counter
    fresh: dict[str, Const] = field(default_factory=dict)
    counts: Counter = field(default_factory=Counter)

    def term(self, var: str) -> Const | Var:
        while var in self.alias:
            var = self.alias[var]
        if var in self.const:
            return Const(self.const[var])
        if self.mode == "tell" and (Var(var).event or self.bound.get(var) == quant.INDEF):
            if var not in self.fresh:
                kind = "event" if Var(var).event else "anon"
                self.counts[kind] += 1
                self.fresh[var] = Const(lf.fresh_id(kind, self.counts[kind]), kind)
            return self.fresh[var]
        return Var(var)


def eventive(r: Reading) -> bool:
    """A reading is about an event only if a predicate other than the unknown-word fallback takes the sentence event."""
    return any(ep.args.get("ARG0") == r.index and ep.pred != "unknown" for ep in r.eps)


def compile_reading(r: Reading) -> lf.LF:
    sf = r.props[r.index].get("SF")
    if sf not in ("prop", "ques"):
        return lf.Refusal("UNSUPPORTED_FORCE", str(sf))
    quants = [ep for ep in r.eps if quant.is_quantifier(ep)]
    bound = {ep.args["ARG0"]: ep.pred for ep in quants}
    alias = copula.plan(r.eps, bound)
    main_label = r.qeq[r.top]
    main_vars = {v for ep in r.eps if ep.label == main_label for v in ep.args.values()}
    universal_top = [
        q for q in quants
        if q.pred in quant.UNIVERSAL and q.args["ARG0"] in main_vars and q.args["ARG0"] not in alias
    ]
    body = _restricted(r, quants, universal_top)
    usage = Counter(v for ep in r.eps for v in ep.args.values())
    mode = "ask" if sf == "ques" else "rule" if universal_top else "tell"
    ctx = Ctx(mode, bound, alias, names.plan(r), usage)
    if mode == "rule":
        head = _map(ctx, [ep for i, ep in enumerate(r.eps) if i not in body])
        if isinstance(head, lf.Refusal):
            return head
        tail = _map(ctx, [ep for i, ep in enumerate(r.eps) if i in body])
        if isinstance(tail, lf.Refusal):
            return tail
        return lf.Rule(head, tail)
    atoms = _map(ctx, r.eps)
    if isinstance(atoms, lf.Refusal):
        return atoms
    if mode == "tell":
        return lf.Tell(atoms)
    wanted = tuple(ctx.term(v) for v, p in bound.items() if p in quant.WH)
    return lf.Ask(atoms, wanted)


def _restricted(r: Reading, quants: list[EP], universal_top: list[EP]) -> set[int]:
    """Indices of predications inside a universal's restriction, including nested indefinites' restrictions."""

    def restriction(q: EP) -> list[int]:
        target = r.qeq.get(q.args["RSTR"])
        return [i for i, ep in enumerate(r.eps) if ep.label == target]

    body: set[int] = set()
    for q in universal_top:
        frontier = restriction(q)
        while frontier:
            i = frontier.pop()
            if i in body:
                continue
            body.add(i)
            for q2 in quants:
                if q2.args["ARG0"] in r.eps[i].args.values():
                    frontier += restriction(q2)
    return body


def _map(ctx: Ctx, eps: list[EP]) -> tuple[Atom, ...] | lf.Refusal:
    atoms: list[Atom] = []
    for ep in eps:
        for fam in FAMILIES:
            got = fam.map_ep(ctx, ep)
            if got is None:
                continue
            if isinstance(got, lf.Refusal):
                return got
            atoms.extend(got)
            break
        else:
            return lf.Refusal("UNSUPPORTED_PREDICATE", ep.pred)
    return tuple(atoms)


def choose(readings: list[Reading], store_preds: set[str]) -> tuple[int, lf.LF]:
    """The eventive reading whose predicates overlap the store most; ties go to the parser's order."""
    cands = [(i, compile_reading(r)) for i, r in enumerate(readings) if eventive(r)]
    if not cands:
        return 0, lf.Refusal("NO_EVENT_READING", "none of the readings has a predicate on the sentence event")
    ok = [(i, x) for i, x in cands if not isinstance(x, lf.Refusal)]
    if not ok:
        return cands[0]
    return max(ok, key=lambda t: (len(_preds(t[1]) & store_preds), -t[0]))


def _preds(x: lf.LF) -> set[str]:
    if isinstance(x, lf.Tell):
        return {a.pred for a in x.atoms}
    if isinstance(x, lf.Rule):
        return {a.pred for a in x.head + x.body}
    if isinstance(x, lf.Ask):
        return {a.pred for a in x.body}
    return set()

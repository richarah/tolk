"""Reading to logical form. The families in tolk/rules each map one predicate; this module decides scope, polarity and variable kinds."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

from tolk import lf
from tolk.lf import Atom, Const, Var
from tolk.rules import content, copula, modifiers, names, neg, quant
from tolk.sem import EP, Reading

FAMILIES = (names, quant, neg, copula, modifiers, content)
Lookup = Callable[[str], set[str]]


@dataclass
class Ctx:
    mode: str  # ask, tell or rule
    side: str  # where the atoms being mapped go: tell, ask, head or body
    bound: dict[str, str]
    alias: dict[str, str]
    const: dict[str, str]
    negated: set[str]
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

    def no_event(self, ep: EP) -> Const | Var:
        # A negated event is empty in a stored fact, and unknown in a body where it must match any event.
        if self.side in ("tell", "head"):
            return Const("", lf.NO_EVENT)
        return Var(f"e{ep.args['ARG0']}n")


def eventive(r: Reading) -> bool:
    """A reading is about an event only if a predicate other than the unknown-word fallback takes the sentence event."""
    return any(ep.args.get("ARG0") == r.index and ep.pred != "unknown" for ep in r.eps)


def compile_reading(r: Reading, lookup: Lookup | None = None) -> lf.LF:
    sf = r.props[r.index].get("SF")
    if sf not in ("prop", "ques"):
        return lf.Refusal("UNSUPPORTED_FORCE", str(sf))
    quants = [ep for ep in r.eps if quant.is_quantifier(ep)]
    main_labels = _main_labels(r)
    main = [ep for ep in r.eps if ep.label in main_labels]
    main_vars = {v for ep in main for v in ep.args.values()}
    subjects = {ep.args["ARG1"] for ep in main if "ARG1" in ep.args}
    # A bare plural is universal only as a statement's subject; anywhere else it is an indefinite.
    bound = {ep.args["ARG0"]: ep.pred for ep in quants}
    for v, p in bound.items():
        if p == "udef_q" and v not in subjects:
            bound[v] = quant.INDEF
    alias = copula.plan(r.eps, bound)
    const = names.plan(r)
    for q in quants:
        if q.pred == quant.DEFINITE:
            resolved = _definite(r, q, lookup)
            if isinstance(resolved, lf.Refusal):
                return resolved
            const[q.args["ARG0"]] = resolved
    for ep in main:
        if copula.is_copula(ep) and ep.args["ARG1"] in const and ep.args["ARG2"] in const and sf == "prop":
            return lf.Same(Const(const[ep.args["ARG1"]], "named"), Const(const[ep.args["ARG2"]], "named"))
    negated = _negated(r, quants, alias, bound)
    universal_top = [
        q for q in quants
        if q.pred in quant.UNIVERSAL and q.args["ARG0"] in main_vars and q.args["ARG0"] not in alias
        and bound[q.args["ARG0"]] == q.pred
    ]
    if sf == "prop":
        # Under negation an indefinite object has narrow scope: no X is V-ed is every X is not V-ed.
        universal_top += [
            q for q in quants
            if bound[q.args["ARG0"]] == quant.INDEF and q.args["ARG0"] not in alias and q.args["ARG0"] not in subjects
            and any(ep.label in negated and q.args["ARG0"] in ep.args.values() for ep in r.eps)
        ]
    body = _restricted(r, quants, universal_top)
    if any(q.pred == "_every_q" and q in universal_top for q in quants) and any(
        ep.label in negated and ep.pred != "neg" for i, ep in enumerate(r.eps) if i not in body
    ):
        return lf.Refusal("SCOPE_AMBIGUOUS", "every under negation means all-not or not-all")
    if any(q.pred == "_no_q" and q.args["ARG0"] in main_vars for q in quants):
        # "No X V" negates the whole head: the verb, and any complement the copula moved onto the subject.
        negated |= {ep.label for i, ep in enumerate(r.eps) if i not in body}
    mode = "ask" if sf == "ques" else "rule" if universal_top else "tell"
    ctx = Ctx(mode, mode, bound, alias, const, negated, Counter(v for ep in r.eps for v in ep.args.values()))
    wanted = tuple(ctx.term(v) for v, p in bound.items() if p in quant.WH)
    if any(not isinstance(w, Var) for w in wanted):
        return lf.Refusal("WH_BOUND_TO_CONSTANT", str(wanted))
    if mode == "rule":
        ctx.side = "head"
        head = _map(ctx, [ep for i, ep in enumerate(r.eps) if i not in body])
        if isinstance(head, lf.Refusal):
            return head
        ctx.side = "body"
        tail = _map(ctx, [ep for i, ep in enumerate(r.eps) if i in body])
        if isinstance(tail, lf.Refusal):
            return tail
        out = lf.Rule(head, tail)
    else:
        atoms = _map(ctx, r.eps)
        if isinstance(atoms, lf.Refusal):
            return atoms
        out = lf.Tell(atoms) if mode == "tell" else lf.Ask(atoms, wanted)
    unconsumed = _unconsumed(ctx, quants, out, mode)
    if unconsumed:
        return unconsumed
    if mode == "tell" and r.props[r.index].get("TENSE") == "past":
        out = lf.Tell(out.atoms + (Atom("tense", (ctx.term(r.index), Const("past", "value"))),))
    unbound = _unbound(out, bound)
    return lf.Refusal("UNBOUND_VARIABLE", unbound) if unbound else out


def _main_labels(r: Reading) -> set[str]:
    """The top clause, and any clause a neg at the top points at."""
    labels = {r.qeq[r.top]}
    grew = True
    while grew:
        more = {r.qeq.get(ep.args["ARG1"], ep.args["ARG1"]) for ep in r.eps if ep.pred == "neg" and ep.label in labels}
        grew = not more <= labels
        labels |= more
    return labels


def _unconsumed(ctx: Ctx, quants: list[EP], out: lf.LF, mode: str) -> lf.Refusal | None:
    """A reading compiles only if nothing in it was silently dropped."""
    atoms = _atoms(out)
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


def _negated(r: Reading, quants: list[EP], alias: dict[str, str], bound: dict[str, str]) -> set[str]:
    """Labels of the clauses a neg predication negates, widened to a copula complement's restriction."""
    negated = neg.labels(r)
    for ep in r.eps:
        if copula.is_copula(ep) and ep.label in negated and ep.args["ARG2"] in alias:
            for q in quants:
                if q.args["ARG0"] == ep.args["ARG2"]:
                    negated.add(r.qeq.get(q.args["RSTR"]))
    return negated


def _definite(r: Reading, q: EP, lookup: Lookup | None) -> str | lf.Refusal:
    if lookup is None:
        return lf.Refusal("DEFINITE_NEEDS_STORE", q.pred)
    var = q.args["ARG0"]
    target = r.qeq.get(q.args["RSTR"])
    restr = [ep for ep in r.eps if ep.label == target and ep.args.get("ARG0") == var]
    cands = set.intersection(*(lookup(ep.pred) for ep in restr)) if restr else set()
    if len(cands) != 1:
        return lf.Refusal("DEFINITE_MATCHES", f"{len(cands)} known things match")
    return next(iter(cands))


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


def _unbound(x: lf.LF, bound: dict[str, str]) -> str:
    """Names of variables that no quantifier binds and that are not events. Such a variable would be silently ignored."""
    keys = {t.key for a in _atoms(x) for t in a.args if isinstance(t, Var)}
    names_ = sorted(k for k in keys if not Var(k).event and k not in bound)
    return ", ".join(names_)


def _atoms(x: lf.LF) -> list[Atom]:
    if isinstance(x, lf.Tell):
        return list(x.atoms)
    if isinstance(x, lf.Rule):
        return list(x.head + x.body)
    if isinstance(x, lf.Ask):
        return list(x.body)
    return []


def choose(readings: list[Reading], store_preds: set[str], lookup: Lookup | None = None) -> tuple[int, lf.LF]:
    """The eventive reading whose predicates overlap the store most; ties go to the parser's order."""
    cands = [(i, compile_reading(r, lookup)) for i, r in enumerate(readings) if eventive(r)]
    if not cands:
        return 0, lf.Refusal("NO_EVENT_READING", "none of the readings has a predicate on the sentence event")
    ok = [(i, x) for i, x in cands if not isinstance(x, lf.Refusal)]
    if not ok:
        return cands[0]
    return max(ok, key=lambda t: (len(_preds(t[1]) & store_preds), -_gaps(readings[t[0]]), -t[0]))


def _gaps(r: Reading) -> int:
    """Stretches of the sentence, more than one character wide, that no predication spans. A word the reading swallowed leaves one."""
    spans = sorted((ep.cfrom, ep.cto) for ep in r.eps if ep.cfrom >= 0)
    gaps, end = 0, 0
    for start, stop in spans:
        gaps += start - end > 1
        end = max(end, stop)
    return gaps


def _preds(x: lf.LF) -> set[tuple[str, int]]:
    """Predicate and arity of each positive atom. Arity separates a verb's two-place use from its three-place use."""
    return {(a.pred, len(a.args)) for a in _atoms(x) if a.positive}

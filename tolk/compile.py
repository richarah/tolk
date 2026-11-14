"""Reading to logical form, and the choice among readings. The families in tolk/rules each map one predicate."""

from collections import Counter

from tolk import lf
from tolk.lf import Atom, Const, Var
from tolk.rules import check, content, copula, describe, modifiers, names, neg, quant, scope
from tolk.rules.ctx import Ctx, Lookup
from tolk.sem import EP, Reading

FAMILIES = (names, quant, neg, copula, modifiers, content)


def eventive(r: Reading) -> bool:
    """A reading is about an event only if a predicate other than the unknown-word fallback takes the sentence event."""
    return any(ep.args.get("ARG0") == r.index and ep.pred != "unknown" for ep in r.eps)


def compile_reading(r: Reading, lookup: Lookup | None = None) -> lf.LF:
    sf = r.props[r.index].get("SF")
    if sf not in ("prop", "ques"):
        return lf.Refusal("UNSUPPORTED_FORCE", str(sf))
    unsaid = check.tense(r)
    if unsaid:
        return unsaid
    quants = [ep for ep in r.eps if quant.is_quantifier(ep)]
    main_labels = scope.main_labels(r)
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
            resolved = scope.definite(r, q, lookup)
            if isinstance(resolved, lf.Refusal):
                return resolved
            const[q.args["ARG0"]] = resolved
    if sf == "ques":
        described = describe.entity(r, main, bound, const)
        if described is not None:
            return lf.Describe(Const(described))
    for ep in main:
        if copula.is_copula(ep) and ep.args["ARG1"] in const and ep.args["ARG2"] in const and sf == "prop":
            return lf.Same(Const(const[ep.args["ARG1"]], "named"), Const(const[ep.args["ARG2"]], "named"))
    negated = scope.negated(r, quants, alias, bound)
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
    if sf == "ques" and any(q.pred in quant.UNIVERSAL and bound[q.args["ARG0"]] == q.pred for q in quants):
        return lf.Refusal("UNIVERSAL_QUESTION", "a question over every or no thing would be answered as a question over some")
    body = scope.restricted(r, quants, universal_top)
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
        if not tail:
            # A universal over a named thing has nothing to range over; the name reading of a bare plural lands here.
            return lf.Refusal("EMPTY_RULE_BODY", "the restriction has no atom")
        out = lf.Rule(head, tail)
    else:
        atoms = _map(ctx, r.eps)
        if isinstance(atoms, lf.Refusal):
            return atoms
        out = lf.Tell(atoms) if mode == "tell" else lf.Ask(atoms, wanted)
    unconsumed = check.unconsumed(ctx, quants, out, mode)
    if unconsumed:
        return unconsumed
    if mode == "tell" and r.props[r.index].get("TENSE") == "past":
        out = lf.Tell(out.atoms + (Atom("tense", (ctx.term(r.index), Const("past", "value"))),))
    unbound = check.unbound(out, bound)
    return lf.Refusal("UNBOUND_VARIABLE", unbound) if unbound else out


def _map(ctx: Ctx, eps: list[EP]) -> tuple[Atom, ...] | lf.Refusal:
    atoms: list[Atom] = []
    for ep in eps:
        if content.CONJUNCTION.fullmatch(ep.pred):
            # Checked before the families: the families would take a conjunction of two events for an event modifier.
            return lf.Refusal("COORDINATION", ep.pred)
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


def choose(readings: list[Reading], store_preds: set[str], lookup: Lookup | None = None) -> tuple[int, lf.LF]:
    """Choose one reading. The order of criteria is numbered in DECISIONS.md ("Reading choice") and is applied here and nowhere else.

    0. Only eventive readings are candidates.
    1. Refusals, in parser order: a reading refusal is skipped; a final refusal ends the search. If no reading compiled
       before it, the sentence is refused with it; otherwise only the readings before it compete.
    2. Store overlap: the most (predicate, arity) pairs already in the store.
    3. Swallowed words: the fewest words that most compiled readings span and this one leaves out.
    4. Parser order.
    """
    cands = [(i, compile_reading(r, lookup)) for i, r in enumerate(readings) if eventive(r)]
    if not cands:
        return 0, lf.Refusal("NO_EVENT_READING", "none of the readings has a predicate on the sentence event")
    ok = []
    for i, x in cands:
        if not isinstance(x, lf.Refusal):
            ok.append((i, x))
        elif lf.is_final(x):
            if not ok:
                return i, x
            break
    if not ok:
        return cands[0]
    voters = [readings[i] for i, _ in ok]
    return max(ok, key=lambda t: (len(_preds(t[1]) & store_preds), -_swallowed(readings[t[0]], voters), -t[0]))


def _swallowed(r: Reading, voters: list[Reading]) -> int:
    """Words that most voting readings give a predication to and r leaves out. Auxiliaries are spanned by few readings, so they do not count.
    Only readings that compile vote: a refused one may span a word with a predicate nothing can use, such as an ellipsis."""
    spans = [{p for ep in v.eps if ep.cfrom >= 0 for p in range(ep.cfrom, ep.cto)} for v in voters]
    mine = {p for ep in r.eps if ep.cfrom >= 0 for p in range(ep.cfrom, ep.cto)}
    gone = sorted(p for p in set().union(*spans) - mine if 2 * sum(p in s for s in spans) > len(voters))
    return sum(1 for n, p in enumerate(gone) if n == 0 or p - gone[n - 1] > 1)


def _preds(x: lf.LF) -> set[tuple[str, int]]:
    """Predicate and arity of each positive atom. Arity separates a verb's two-place use from its three-place use."""
    return {(a.pred, len(a.args)) for a in check.atoms_of(x) if a.positive}

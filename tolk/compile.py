"""Reading to logical form. The families in tolk/rules each map one predicate; `choice` says which reading to compile."""

import dataclasses
from collections import Counter

from tolk import choice, lf
from tolk.lf import Atom, Const, Var
from tolk.rules import check, claims, comparatives, conditional, content, coordination, copula, describe, modifiers, names, neg, numbers, pronouns, post, quant, scope, temporal
from tolk.rules.ctx import Ctx, Lookup
from tolk.sem import EP, Reading

# Predicates the grammar uses for bookkeeping of the grammar, seen only in readings that are not the sentence: ellipsis, an implied place, a
# subordinator, a modifier of nothing, an apposition. A reading that has one is unusable; it is not a meaning the store cannot hold.
ARTIFACTS = {"ellipsis_ref", "place_n", "subord", "mod", "appos", "id"}
FAMILIES = (names, pronouns, numbers, quant, neg, copula, conditional, coordination, temporal, claims, comparatives, modifiers, content)


def compile_reading(r: Reading, lookup: Lookup | None = None, history: pronouns.History | None = None) -> lf.LF:
    sf = r.props[r.index].get("SF")
    if sf not in ("prop", "ques"):
        return lf.Refusal("UNSUPPORTED_FORCE", str(sf))
    unsaid = check.tense(r)
    if unsaid:
        return unsaid
    for ep in r.eps:
        if quant.DEMONSTRATIVE.fullmatch(ep.pred):
            return lf.Refusal("DEMONSTRATIVE", ep.pred)
    quants = [ep for ep in r.eps if quant.is_quantifier(ep)]
    cards = numbers.cardinals(r)
    if isinstance(cards, lf.Refusal):
        return cards
    many = numbers.how_many(r)
    main_labels = scope.main_labels(r)
    main = [ep for ep in r.eps if ep.label in main_labels]
    main_vars = {v for ep in main for v in ep.args.values()}
    subjects = {ep.args["ARG1"] for ep in main if "ARG1" in ep.args}
    # A bare plural is universal only as a statement's subject; anywhere else it is an indefinite.
    bound = {ep.args["ARG0"]: ep.pred for ep in quants}
    for v, p in bound.items():
        if p == "udef_q" and (v not in subjects or v in cards or (many and v == many[0])):
            bound[v] = quant.INDEF
    conjs = coordination.find(r)
    for c in conjs:
        if c.nominal:
            bound[c.group] = quant.INDEF  # a group of things is not a generic: it stands for its members
    compared = comparatives.plan(r)
    if isinstance(compared, lf.Refusal):
        return compared
    if sf == "ques" and (extreme := comparatives.superlative(r)):
        return lf.Extreme(extreme)
    alias = copula.plan(r.eps, bound)
    const = names.plan(r)
    resolved = pronouns.plan(r, const, history)
    if isinstance(resolved, lf.Refusal):
        return resolved
    const.update(resolved[0])
    notes = resolved[1]
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
    cond = conditional.find(r, main)
    negated = scope.negated(r, quants, alias, bound)
    universal_top = [
        q for q in quants
        if q.pred in quant.UNIVERSAL and q.args["ARG0"] in main_vars and q.args["ARG0"] not in alias
        and bound[q.args["ARG0"]] == q.pred
    ]
    if cond is not None and (sf == "ques" or universal_top):
        return lf.Refusal("UNSUPPORTED_PREDICATE", cond.pred)
    # Under negation an indefinite object has narrow scope: no X is V-ed is every X is not V-ed.
    narrow = [
        q for q in quants
        if bound[q.args["ARG0"]] == quant.INDEF and q.args["ARG0"] not in alias and q.args["ARG0"] not in subjects
        and any(ep.label in negated and q.args["ARG0"] in ep.args.values() for ep in r.eps)
    ]
    generic = any(q.pred == "udef_q" for q in universal_top)
    if cond is None:
        universal_top += narrow
    body = scope.restricted(r, quants, universal_top)
    if cond is not None:
        body = scope.clause(r, quants, conditional.labels(r, cond)[0])
    if any(q.pred in ("_every_q", "_all_q", "_each_q") and q in universal_top for q in quants) and any(
        ep.label in negated and ep.pred != "neg" for i, ep in enumerate(r.eps) if i not in body
    ):
        return lf.Refusal("SCOPE_AMBIGUOUS", "every under negation means all-not or not-all")
    if any(q.pred == "_no_q" and q.args["ARG0"] in main_vars for q in quants):
        # "No X V" negates the whole head: the verb, and any complement the copula moved onto the subject.
        negated |= {ep.label for i, ep in enumerate(r.eps) if i not in body}
    mode = "rule" if universal_top or cond is not None else "ask" if sf == "ques" else "tell"
    if mode == "rule" and any(c.nominal or c.op == "or" for c in conjs):
        return lf.Refusal("COORDINATION", "a group or an or in a rule")
    if mode == "rule" and temporal.find(r):
        return lf.Refusal("UNSUPPORTED_PREDICATE", "before or after in a rule: the order of the events a rule makes is not stored")
    if cards and mode == "rule":
        return lf.Refusal("UNSUPPORTED_PREDICATE", "card in a rule: the number of things a rule makes is not stored")
    if len(cards) > 1 and mode == "ask":
        return lf.Refusal("UNSUPPORTED_PREDICATE", "card: one number per question")
    ctx = Ctx(mode, mode, bound, alias, const, negated, Counter(v for ep in r.eps for v in ep.args.values()), compared=compared)
    held = claims.find(r)
    inside: set[int] = set()
    if held:
        if mode == "rule" or len(held) > 1:
            return lf.Refusal("UNSUPPORTED_PREDICATE", "a claim in a rule, or a claim inside a claim: " + held[0][0].pred)
        verb, label = held[0]
        inside = scope.clause(r, quants, label)
        ctx.claim[verb.args["ARG2"]] = Const(lf.fresh_id("claim", 1), "claim") if mode == "tell" else Var("claim1")
    wanted = tuple(ctx.term(v) for v, p in bound.items() if p in quant.WH and not (many and v == many[1]))
    if sf == "ques" and mode == "rule" and (wanted or many or cards):
        return lf.Refusal("UNIVERSAL_QUESTION", "a question that asks for things, or counts them, over every thing")
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
        if not head:
            return lf.Refusal("UNCONSUMED", "a rule with no conclusion")
        if any(not a.positive and any(isinstance(t, Var) and bound.get(t.key) == quant.INDEF for t in a.args) for a in tail):
            # not (exists y: p(y) and q(y)) cannot be a negated body atom next to p(y): that would mean some y with not q(y).
            return lf.Refusal("NEGATED_INDEFINITE", "a negated clause in a rule body introduces a new thing")
        if not tail:
            # A universal over a named thing has nothing to range over; the name reading of a bare plural lands here.
            return lf.Refusal("EMPTY_RULE_BODY", "the restriction has no atom")
        out = lf.Rule(head, tail, notes=notes, kind="default" if generic and cond is None else "strict")
        if sf == "ques":
            return lf.Every(head, tail)
    else:
        atoms = _map(ctx, [ep for i, ep in enumerate(r.eps) if i not in inside])
        if isinstance(atoms, lf.Refusal):
            return atoms
        ordered = temporal.order(ctx, r)
        if isinstance(ordered, lf.Refusal):
            return ordered
        content_atoms = _map(ctx, [r.eps[i] for i in sorted(inside)]) if inside else ()
        if isinstance(content_atoms, lf.Refusal):
            return content_atoms
        alts = coordination.distribute(ctx, (post.expand(ctx, atoms, cards) if mode == "tell" else atoms) + ordered, conjs)
        if isinstance(alts, lf.Refusal):
            return alts
        if mode == "tell":
            out = lf.Tell(alts[0], notes=notes, claims=tuple((ctx.claim[verb.args["ARG2"]], content_atoms) for verb, _ in held))
        else:
            counted, at_least = (Var(many[0]), 0) if many else next(((Var(v), n) for v, n in cards.items()), (None, 0))
            out = lf.Ask(alts[0], wanted, notes, counted, at_least, claims=tuple((ctx.claim[verb.args["ARG2"]], content_atoms) for verb, _ in held),
                         alternatives=tuple(alts) if len(alts) > 1 else ())
    probe = lf.Ask(tuple(a for alt in out.alternatives for a in alt), out.wanted) if isinstance(out, lf.Ask) and out.alternatives else out
    groups = {c.group for c in conjs if c.nominal}
    unconsumed = check.unconsumed(ctx, [q for q in quants if not (many and q.args["ARG0"] == many[1]) and q.args["ARG0"] not in groups], probe, mode)
    if unconsumed:
        return unconsumed
    if isinstance(out, (lf.Tell, lf.Rule)):
        out = dataclasses.replace(out, mentions=post.mentions(r, ctx, [q for q in quants if q.args["ARG0"] not in cards], out))
    if mode == "tell":
        out = dataclasses.replace(out, atoms=out.atoms + post.tenses(ctx, r, out.atoms))
    elif isinstance(out, lf.Rule):
        out = dataclasses.replace(out, head=out.head + post.tenses(ctx, r, out.head))
    elif isinstance(out, lf.Ask):
        out = dataclasses.replace(out, tenses=post.asked_tenses(ctx, r, out))
    unbound = check.unbound(out, bound)
    return lf.Refusal("UNBOUND_VARIABLE", unbound) if unbound else out


def _map(ctx: Ctx, eps: list[EP]) -> tuple[Atom, ...] | lf.Refusal:
    atoms: list[Atom] = []
    for ep in eps:
        if ep.pred == "unknown":
            # The grammar's fallback for words it could not analyse in this reading; another reading may do better.
            return lf.Refusal("FALLBACK_PARSE", "a word was not analysed by the grammar")
        if coordination.CONJUNCTION.fullmatch(ep.pred):
            # Checked before the families, which would take a conjunction of two events for an event modifier.
            got = coordination.map_ep(ctx, ep)
            atoms.extend(got)
            continue
        for fam in FAMILIES:
            got = fam.map_ep(ctx, ep)
            if got is None:
                continue
            if isinstance(got, lf.Refusal):
                return got
            atoms.extend(got)
            break
        else:
            return lf.Refusal("GRAMMAR_ARTIFACT" if ep.pred in ARTIFACTS else "UNSUPPORTED_PREDICATE", ep.pred)
    return tuple(atoms)


def choose(readings: list[Reading], store_preds: set, lookup: Lookup | None = None,
           history: pronouns.History | None = None, after: int = 0) -> tuple[int, lf.LF]:
    """Compile the reading `choice.preferred` puts first, and return what it gives, refusal or not. Only when readings are tied
    on every measure does compile decide among them, in parser order: a reading refusal passes the tie to the next reading. With
    `after` (the wide parse) the readings before it were refused already and are not compiled again: the first tied reading from there
    on that compiles to something is the one, whatever kind of refusal the earlier ones gave."""
    tied = choice.preferred(readings, store_preds)
    if not tied:
        return 0, _blame_unknown_word(readings, lf.Refusal("NO_EVENT_READING", "none of the readings has a predicate on the sentence event"))
    first = None
    for i in [i for i in tied if i >= after]:
        x = compile_reading(readings[i], lookup, history)
        if not isinstance(x, lf.Refusal) or (lf.is_final(x) and not after):
            return i, _blame_unknown_word(readings, x) if isinstance(x, lf.Refusal) else x
        first = first or (i, x)
    if first is None:
        return 0, lf.Refusal("NO_EVENT_READING", "no reading beyond the first ones")
    return first[0], _blame_unknown_word(readings, first[1])


def _blame_unknown_word(readings: list[Reading], refusal: lf.Refusal) -> lf.Refusal:
    """A sentence the grammar had to guess a word in, and that cannot be stored, is refused for that word."""
    for r in readings:
        for ep in r.eps:
            m = content.UNKNOWN.fullmatch(ep.pred)
            if m:
                return lf.Refusal("UNKNOWN_WORD", m.group(1))
    return refusal

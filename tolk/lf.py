import json
import re
from dataclasses import dataclass
from itertools import chain, count

# Kinds of constant that the store renames to fresh ids; the prefix is their one home.
FRESH = {"event": "e", "anon": "a", "claim": "claim"}
# A word the grammar did not recognise is stored as _base_pos_unknown; this is the one home of that shape.
UNKNOWN_SENSE = "unknown"
UNKNOWN_PRED = re.compile(rf"_(.+)_([nav])_{UNKNOWN_SENSE}")
# Built-in predicates the system itself states: the tense of an event, and the order of two events.
TENSE = "tense"
MODAL = "modal"
BEFORE = "before"
# Constant standing for the missing event of a negated rule conclusion (present, no modal); its event column is empty. A told negated
# predication has an event of its own (see aspect.py).
NO_EVENT = "empty"


def fresh_id(kind: str, n: int) -> str:
    return f"{FRESH[kind]}{n}"


@dataclass(frozen=True)
class Const:
    id: str
    kind: str = "named"


@dataclass(frozen=True)
class Var:
    key: str

    @property
    def event(self) -> bool:
        return self.key.startswith("e")


Term = Const | Var


@dataclass(frozen=True)
class Atom:
    pred: str
    args: tuple[Term, ...]
    positive: bool = True


@dataclass(frozen=True)
class Tell:
    atoms: tuple[Atom, ...]
    mentions: tuple[tuple[int, str, str], ...] = ()  # (position in the sentence, thing, number), for later pronouns
    notes: tuple[str, ...] = ()  # pronoun resolutions, shown before anything is stored
    claims: tuple[tuple["Const", tuple["Atom", ...]], ...] = ()  # (the claim, what it holds): a clause that someone believes, says, knows


@dataclass(frozen=True)
class Rule:
    head: tuple[Atom, ...]
    body: tuple[Atom, ...]
    mentions: tuple[tuple[int, str, str], ...] = ()
    notes: tuple[str, ...] = ()
    kind: str = "strict"  # "default" for a bare plural generic: it holds unless something overrides it

    @property
    def creates(self) -> tuple[Var, ...]:
        # A head variable absent from the body is made by the rule, so each binding gets a separate thing.
        body_vars = {t for a in self.body for t in a.args if isinstance(t, Var)}
        seen: list[Var] = []
        for a in self.head:
            for t in a.args:
                if isinstance(t, Var) and t not in body_vars and t not in seen:
                    seen.append(t)
        return tuple(seen)


@dataclass(frozen=True)
class Ask:
    body: tuple[Atom, ...]
    wanted: tuple[Var, ...]
    notes: tuple[str, ...] = ()
    count: Var | None = None  # count the distinct things this variable takes
    atleast: int = 0  # with count: 0 asks how many; n asks whether there are at least n
    claims: tuple[tuple["Var", tuple["Atom", ...]], ...] = ()  # (the claim asked about, the content it must hold exactly)
    tenses: tuple[tuple[Var, str], ...] = ()  # events of the question that must be past, or present; a fact without an event is either
    modals: tuple[tuple[Var, str], ...] = ()  # per event of the question, the modal it must have ("can", ...), or "" for none
    alternatives: tuple[tuple[Atom, ...], ...] = ()  # an or: the question is answered by each alternative body, and any Yes wins
    claims_join: str = ""  # with several claims: "and" (each claim must be held) or "or" (any one of them); "" for one claim


@dataclass(frozen=True)
class Every:
    """A question about every thing of a kind: does the conclusion follow from the restriction, for a fresh thing?"""
    head: tuple[Atom, ...]
    body: tuple[Atom, ...]


@dataclass(frozen=True)
class Same:
    a: Const
    b: Const


@dataclass(frozen=True)
class Describe:
    entity: Const


@dataclass(frozen=True)
class DescribeKind:
    pred: str  # What is a fish? What is fish? What are birds?: the predicate of the noun asked about


@dataclass(frozen=True)
class Extreme:
    pred: str  # the adjective a superlative question is about: Who is the tallest?


@dataclass(frozen=True)
class Refusal:
    code: str
    detail: str


LF = Tell | Rule | Ask | Every | Same | Describe | DescribeKind | Extreme | Refusal

# The one home of refusal codes. "final": the sentence was understood and the store cannot hold what it means,
# so the reading search ends. "reading": this reading is unusable, so the next one is tried.
REFUSALS = {
    "ARGUMENT_GAP": "reading", "FALLBACK_PARSE": "reading", "EMPTY_RULE_BODY": "reading", "TOO_MANY_ARGUMENTS": "reading",
    "UNBOUND_VARIABLE": "reading", "DEMONSTRATIVE": "reading", "GRAMMAR_ARTIFACT": "reading", "UNCONSTRAINED_WANTED": "reading", "UNCONSUMED": "reading", "UNEXPRESSED_OBJECT": "reading",
    "UNEXPRESSED_SUBJECT": "reading", "WH_BOUND_TO_CONSTANT": "reading",
    "CONTRADICTS": "final", "COORDINATION": "final", "DEFINITE_MATCHES": "final", "DEFINITE_NEEDS_STORE": "final",
    "IDENTITY_NOT_YET": "final", "NEGATED_INDEFINITE": "final", "NO_EVENT_READING": "final", "SCOPE_AMBIGUOUS": "final",
    "UNIVERSAL_QUESTION": "final", "UNKNOWN_WORD": "final", "UNSAFE_NEGATION": "final",
    "NEGATION_CYCLE": "final", "POSSIBLE_TYPO": "final", "AMBIGUOUS_PRONOUN": "final", "NO_ANTECEDENT": "final", "UNSUPPORTED_ASPECT": "final", "UNSUPPORTED_FORCE": "final",
    "UNSUPPORTED_PREDICATE": "final", "UNSUPPORTED_QUANTIFIER": "final", "UNSUPPORTED_TENSE": "final",
}


def is_final(r: Refusal) -> bool:
    return REFUSALS[r.code] == "final"

THING_NAMES = ("X", "Y", "Z", "U", "V", "W")


def show(x: LF) -> str:
    text = _show(x)
    claims = getattr(x, "claims", ())
    if claims:
        names = _namer(x)
        for ref, atoms in claims:
            text += f"\n{'claim':<6} {names(ref) if isinstance(ref, Var) else ref.id} = " + ", ".join(_atom(a, names) for a in atoms)
    notes = getattr(x, "notes", ())
    return "\n".join([text] + [f"{'note':<6} {n}" for n in notes])


def _show(x: LF) -> str:
    if isinstance(x, Refusal):
        return f"refuse {x.code}: {x.detail}"
    if isinstance(x, Same):
        return f"{'same':<6} {x.a.id} = {x.b.id}"
    if isinstance(x, Describe):
        return f"describe {x.entity.id}"
    if isinstance(x, DescribeKind):
        return f"describe kind {x.pred}"
    if isinstance(x, Extreme):
        return f"extreme {x.pred}"
    names = _namer(x)
    if isinstance(x, Tell):
        return "\n".join(f"{'tell':<6} {_atom(a, names)}" for a in x.atoms)
    if isinstance(x, Every):
        return f"{'every':<6} {', '.join(_atom(a, names) for a in x.head)} :- {', '.join(_atom(a, names) for a in x.body)}"
    if isinstance(x, Rule):
        marked: set[Var] = set()
        head = ", ".join(_atom(a, names, x.creates, marked) for a in x.head)
        body = ", ".join(_atom(a, names) for a in x.body)
        return f"{x.kind if x.kind == 'default' else 'rule':<6} {head} :- {body}"
    body = " | ".join(", ".join(_atom(a, names) for a in alt) for alt in (x.alternatives or (x.body,)))
    past = "".join(f"  [{names(v)} past]" for v, t in x.tenses if t == "past")
    body += past + "".join(f"  [{names(v)} {k}]" for v, k in x.modals if k)
    if x.count is not None:
        kind = "count" if not x.atleast else f"ask >={x.atleast}"
        return f"{kind} {names(x.count)}  {body}"
    column = " ".join(names(v) for v in x.wanted) + "  " if x.wanted else "   "
    return f"ask {column}{body}"


def _namer(x: LF):
    """Printed names follow first appearance in the printed text, separately for things and events."""
    table: dict[str, str] = {}
    thing_n = chain(THING_NAMES, (f"X{i}" for i in count(1)))
    event_n = count(0)

    def name(v: Var) -> str:
        if v.key not in table:
            if v.event:
                n = next(event_n)
                table[v.key] = "E" if n == 0 else f"E{n}"
            else:
                table[v.key] = next(thing_n)
        return table[v.key]

    for v in _order(x):
        name(v)
    return name


def _order(x: LF) -> list[Var]:
    if isinstance(x, Ask):
        atoms = x.body + tuple(a for _, claimed in x.claims for a in claimed)
        lead = list(x.wanted) + ([x.count] if x.count is not None else []) + [ref for ref, _ in x.claims]
    elif isinstance(x, (Rule, Every)):
        atoms, lead = x.head + x.body, []
    elif isinstance(x, Tell):
        atoms, lead = x.atoms + tuple(a for _, claimed in x.claims for a in claimed), []
    else:
        return []
    return lead + [t for a in atoms for t in a.args if isinstance(t, Var)]


def _atom(a: Atom, name, creates=(), marked: set[Var] | None = None) -> str:
    parts = []
    for t in a.args:
        if isinstance(t, Const):
            parts.append(t.id or "_")
            continue
        mark = ""
        if marked is not None and t in creates and t not in marked:
            marked.add(t)
            mark = "!"
        parts.append(name(t) + mark)
    return f"{'' if a.positive else 'not '}{a.pred}({', '.join(parts)})"


def encode_rule(r: Rule) -> str:
    return json.dumps({"head": [_enc(a) for a in r.head], "body": [_enc(a) for a in r.body], "kind": r.kind})


def decode_rule(text: str) -> Rule:
    data = json.loads(text)
    return Rule(tuple(_dec(a) for a in data["head"]), tuple(_dec(a) for a in data["body"]), kind=data.get("kind", "strict"))


def _enc(a: Atom) -> list:
    args = [["c", t.id, t.kind] if isinstance(t, Const) else ["v", t.key] for t in a.args]
    return [a.pred, args, a.positive]


def _dec(a: list) -> Atom:
    args = tuple(Const(t[1], t[2]) if t[0] == "c" else Var(t[1]) for t in a[1])
    return Atom(a[0], args, a[2])

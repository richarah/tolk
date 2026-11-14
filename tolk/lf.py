import json
from dataclasses import dataclass
from itertools import chain, count

# Kinds of constant that the store renames to fresh ids; the prefix is their one home.
FRESH = {"event": "e", "anon": "a"}
# Constant standing for the missing event of a negated predication; its event column is empty.
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


@dataclass(frozen=True)
class Rule:
    head: tuple[Atom, ...]
    body: tuple[Atom, ...]

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


@dataclass(frozen=True)
class Same:
    a: Const
    b: Const


@dataclass(frozen=True)
class Describe:
    entity: Const


@dataclass(frozen=True)
class Refusal:
    code: str
    detail: str


LF = Tell | Rule | Ask | Same | Describe | Refusal

# The one home of refusal codes. "final": the sentence was understood and the store cannot hold what it means,
# so the reading search ends. "reading": this reading is unusable, so the next one is tried.
REFUSALS = {
    "ARGUMENT_GAP": "reading", "EMPTY_RULE_BODY": "reading", "TOO_MANY_ARGUMENTS": "reading",
    "UNBOUND_VARIABLE": "reading", "UNCONSUMED": "reading", "UNEXPRESSED_OBJECT": "reading",
    "UNEXPRESSED_SUBJECT": "reading", "WH_BOUND_TO_CONSTANT": "reading",
    "CONTRADICTS": "final", "COORDINATION": "final", "DEFINITE_MATCHES": "final", "DEFINITE_NEEDS_STORE": "final",
    "IDENTITY_NOT_YET": "final", "NEGATED_QUESTION": "final", "NO_EVENT_READING": "final", "SCOPE_AMBIGUOUS": "final",
    "UNCONSTRAINED_WANTED": "final", "UNIVERSAL_QUESTION": "final", "UNKNOWN_WORD": "final", "UNSAFE_NEGATION": "final",
    "NEGATION_CYCLE": "final", "UNSUPPORTED_ASPECT": "final", "UNSUPPORTED_FORCE": "final",
    "UNSUPPORTED_PREDICATE": "final", "UNSUPPORTED_QUANTIFIER": "final", "UNSUPPORTED_TENSE": "final",
}


def is_final(r: Refusal) -> bool:
    return REFUSALS[r.code] == "final"

THING_NAMES = ("X", "Y", "Z", "U", "V", "W")


def show(x: LF) -> str:
    if isinstance(x, Refusal):
        return f"refuse {x.code}: {x.detail}"
    if isinstance(x, Same):
        return f"{'same':<6} {x.a.id} = {x.b.id}"
    if isinstance(x, Describe):
        return f"describe {x.entity.id}"
    names = _namer(x)
    if isinstance(x, Tell):
        return "\n".join(f"{'tell':<6} {_atom(a, names)}" for a in x.atoms)
    if isinstance(x, Rule):
        marked: set[Var] = set()
        head = ", ".join(_atom(a, names, x.creates, marked) for a in x.head)
        body = ", ".join(_atom(a, names) for a in x.body)
        return f"{'rule':<6} {head} :- {body}"
    body = ", ".join(_atom(a, names) for a in x.body)
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
        atoms, lead = x.body, list(x.wanted)
    elif isinstance(x, Rule):
        atoms, lead = x.head + x.body, []
    elif isinstance(x, Tell):
        atoms, lead = x.atoms, []
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
    return json.dumps({"head": [_enc(a) for a in r.head], "body": [_enc(a) for a in r.body]})


def decode_rule(text: str) -> Rule:
    data = json.loads(text)
    return Rule(tuple(_dec(a) for a in data["head"]), tuple(_dec(a) for a in data["body"]))


def _enc(a: Atom) -> list:
    args = [["c", t.id, t.kind] if isinstance(t, Const) else ["v", t.key] for t in a.args]
    return [a.pred, args, a.positive]


def _dec(a: list) -> Atom:
    args = tuple(Const(t[1], t[2]) if t[0] == "c" else Var(t[1]) for t in a[1])
    return Atom(a[0], args, a[2])

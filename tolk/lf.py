from dataclasses import dataclass
from itertools import chain, count


@dataclass(frozen=True)
class Const:
    id: str


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
class Refusal:
    code: str
    detail: str


LF = Tell | Rule | Ask | Same | Refusal

THING_NAMES = ("X", "Y", "Z", "U", "V", "W")


def show(x: LF) -> str:
    if isinstance(x, Refusal):
        return f"refuse {x.code}: {x.detail}"
    if isinstance(x, Same):
        return f"{'same':<6} {x.a.id} = {x.b.id}"
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
            parts.append(t.id)
            continue
        mark = ""
        if marked is not None and t in creates and t not in marked:
            marked.add(t)
            mark = "!"
        parts.append(name(t) + mark)
    return f"{a.pred}({', '.join(parts)})"

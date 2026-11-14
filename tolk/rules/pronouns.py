"""Pronouns. I and you are two fixed things. A pronoun for a third party is the most recent thing mentioned that agrees in number."""

from typing import TYPE_CHECKING, Callable

from tolk import lf
from tolk.sem import EP, Reading

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

USER, TOLK = "user", "tolk"
# (sentence, entity, number), most recent first: what earlier sentences mentioned.
Mention = tuple[int, str, str]
History = Callable[[], list[Mention]]
SAME = -1  # the sentence group of mentions earlier in the sentence being read


def word(props: dict[str, str]) -> str:
    """How the pronoun is shown in a resolution. The grammar has no gender knowledge, so this only echoes its features."""
    speaker, number, gender = props.get("PERS"), props.get("NUM"), props.get("GEND")
    if speaker == "1":
        return "I"
    if speaker == "2":
        return "you"
    return "they" if number == "pl" else {"f": "she", "m": "he"}.get(gender or "", "it")


def plan(r: Reading, const: dict[str, str], history: History | None) -> tuple[dict[str, str], tuple[str, ...]] | lf.Refusal:
    """Constants for the pronoun variables, and one one note for each pronoun, such as it = (the thing)."""
    out: dict[str, str] = {}
    notes: list[str] = []
    for ep in r.eps:
        if ep.pred != "pron":
            continue
        var, props = ep.args["ARG0"], r.props.get(ep.args["ARG0"], {})
        speaker, number = props.get("PERS"), props.get("NUM", "sg")
        if speaker in ("1", "2"):
            if number == "pl":
                return lf.Refusal("UNSUPPORTED_PREDICATE", "pron")
            out[var] = USER if speaker == "1" else TOLK
        else:
            found = _resolve(r, ep, number, {**const, **out}, history)
            if isinstance(found, lf.Refusal):
                return found
            out[var] = found
        notes.append(f"{word(props)} = {out[var]}")
    return out, tuple(notes)


def _resolve(r: Reading, ep: EP, number: str, known: dict[str, str], history: History | None) -> str | lf.Refusal:
    here = sorted(
        ((q.cfrom, known[q.args["ARG0"]]) for q in r.eps if "RSTR" in q.args and q.args["ARG0"] in known
         and q.args["ARG0"] != ep.args["ARG0"] and 0 <= q.cfrom < ep.cfrom),
        reverse=True)
    ordered = [(SAME, ident, "sg") for _, ident in here] + [(s, e, n) for s, e, n in (history() if history else [])]
    seen: set[str] = set()
    agreeing = []
    for group, ident, num in ordered:
        if num == number and ident not in seen:
            seen.add(ident)
            agreeing.append((group, ident))
    if not agreeing:
        return lf.Refusal("NO_ANTECEDENT", f"nothing agreeing in number ({number}) has been mentioned")
    if len(agreeing) > 1 and agreeing[0][0] == agreeing[1][0]:
        return lf.Refusal("AMBIGUOUS_PRONOUN", f"{agreeing[0][1]} or {agreeing[1][1]}")
    return agreeing[0][1]


def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    return () if ep.pred == "pron" else None

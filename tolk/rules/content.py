"""Content predicates: a noun, verb, adjective or preposition, with its arguments in role order."""

import dataclasses
import re
from collections import Counter
from typing import TYPE_CHECKING

from tolk import lf
from tolk.lf import Atom
from tolk.sem import EP

if TYPE_CHECKING:
    from tolk.rules.ctx import Ctx

ROLES = ("ARG0", "ARG1", "ARG2")
# A word the grammar does not recognise comes as _surface/TAG_u_unknown, TAG being a rough part of speech from the tagger it uses.
UNKNOWN = re.compile(r"_(.+)/([a-z]+)_u_unknown")
# TAG -> (part of speech, suffix to strip to reach the base form). Other tags are refused: their spelling changes are not simple.
TAGS = {"nn": ("n", ""), "nns": ("n", "s"), "jj": ("a", ""), "vb": ("v", ""), "vbp": ("v", ""), "vbz": ("v", "s")}


def known_as(pred: str) -> str | lf.Refusal:
    """The predicate for an unknown word, in the shape of the grammar's predicates: _base_pos_unknown."""
    m = UNKNOWN.fullmatch(pred)
    if m is None or m.group(2) not in TAGS:
        return lf.Refusal("UNKNOWN_WORD", pred)
    lemma, (pos, suffix) = m.group(1), TAGS[m.group(2)]
    if suffix and lemma.endswith(suffix):
        lemma = lemma[: -2] if lemma.endswith(("ches", "shes", "sses", "xes", "zes")) else lemma[: -1]
    return f"_{lemma}_{pos}_{lf.UNKNOWN_SENSE}"

def expressed(values: list[str], usage: Counter) -> tuple[list[bool], int]:
    """An unexpressed argument is an i-variable that nothing else mentions. The flags, and the index of the last expressed argument."""
    flags = [not (v.startswith("i") and usage[v] == 1) for v in values]
    return flags, max((n for n, e in enumerate(flags) if e), default=-1)


def expressed_arity(ep: EP, usage: Counter) -> int:
    return expressed([ep.args[k] for k in ROLES if k in ep.args], usage)[1] + 1


def map_ep(ctx: "Ctx", ep: EP) -> tuple | lf.Refusal | None:
    if not ep.pred.startswith("_"):
        return None
    if "/" in ep.pred:
        renamed = known_as(ep.pred)
        if isinstance(renamed, lf.Refusal):
            return renamed
        ep = dataclasses.replace(ep, pred=renamed)
    if any(k.startswith("ARG") and k not in ROLES for k in ep.args):
        return lf.Refusal("TOO_MANY_ARGUMENTS", ep.pred)
    values = [ep.args[k] for k in ROLES if k in ep.args]
    if any(v.startswith("h") for v in values):
        # A scopal argument is a whole clause; no atom can hold one, so the predication is unused.
        return lf.Refusal("UNSUPPORTED_PREDICATE", ep.pred)
    if not values:
        return lf.Refusal("ARGUMENT_GAP", ep.pred)
    flags, last = expressed(values, ctx.usage)
    if not all(flags[: last + 1]):
        return lf.Refusal("ARGUMENT_GAP", ep.pred)
    is_event = values[0].startswith("e")
    if is_event and len(values) > 1 and not flags[1]:
        return lf.Refusal("UNEXPRESSED_SUBJECT", ep.pred)
    terms = [ctx.term(v) for v in values[: last + 1]]
    positive = ep.label not in ctx.negated
    if is_event and not positive:
        terms[0] = ctx.no_event(ep)
    return (Atom(ep.pred, tuple(terms), positive),)

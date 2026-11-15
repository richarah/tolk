"""Which of the parser's readings to compile. The order is numbered in DECISIONS.md ("Reading choice") and applied only in `preferred`.

Every measure here reads the parser's output alone. Nothing is compiled to measure a reading."""

from collections import Counter

from tolk import lf
from tolk.rules import content, copula, modifiers
from tolk.sem import Reading

GENERIC = "generic"  # the grammar names the entries it falls back on for a word it lacks generic_*


def eventive(r: Reading) -> bool:
    """A reading is about an event only if a predicate other than the unknown-word fallback takes the sentence event."""
    return any(ep.args.get("ARG0") == r.index and ep.pred != "unknown" for ep in r.eps)


def preferred(readings: list[Reading], known: set) -> list[int]:
    """The candidate readings tied for first place, in parser order. Criteria, in order, each applied to what the one before left tied:

    1. Fewest words analysed with a generic entry though the grammar has a real entry for the word.
    2. Most (predicate, arity) pairs already in the store.
    3. Fewest words that most readings give a predication and this one leaves out.
    4. Parser order. Every reading still tied is returned, so that compile can break the tie."""
    cands = candidates(readings)
    keys = {i: _key(readings, i, known, cands) for i in cands}
    best = min(keys.values(), default=())
    return [i for i in cands if keys[i] == best]


def candidates(readings: list[Reading]) -> list[int]:
    return [i for i, r in enumerate(readings) if eventive(r)]


def measures(readings: list[Reading], i: int, known: set) -> tuple[int, int, int]:
    """(generic words, overlap, swallowed stretches) of reading i, as the table in tests/choice_table.json lists them."""
    return _generic(readings, i), _overlap(readings[i], known), _swallowed(readings, i, candidates(readings))


def _key(readings: list[Reading], i: int, known: set, cands: list[int]) -> tuple[int, int, int]:
    return _generic(readings, i), -_overlap(readings[i], known), _swallowed(readings, i, cands)


def _generic(readings: list[Reading], i: int) -> int:
    """Words this reading analyses with a generic entry, where another reading analyses the same word with a real one."""
    real = {(a, b) for j, r in enumerate(readings) if j != i for entry, a, b in r.lex if not entry.startswith(GENERIC)}
    return sum(1 for entry, a, b in readings[i].lex if entry.startswith(GENERIC) and (a, b) in real)


def _overlap(r: Reading, known: set) -> int:
    """Predicates shared with what is known. Known may hold (predicate, arity) pairs, or bare names that match any arity."""
    return sum(1 for p in shapes(r) if p in known or p[0] in known)


def shapes(r: Reading) -> set[tuple[str, int]]:
    """The predicate and arity each lexical predication would be stored with, found as compile finds them."""
    usage = Counter(v for ep in r.eps for v in ep.args.values())
    out = set()
    for ep in r.eps:
        if not ep.pred.startswith("_") or "RSTR" in ep.args or "ARG0" not in ep.args:
            continue
        pred = content.known_as(ep.pred) if "/" in ep.pred else ep.pred
        if isinstance(pred, lf.Refusal):
            continue
        out.add((pred, modifiers.attached_arity(ep) if modifiers.modifies(ep, usage) else content.expressed_arity(ep, usage)))
    return out


def _swallowed(readings: list[Reading], i: int, cands: list[int]) -> int:
    """Stretches of words that most candidates give a content predication and reading i gives none. The copula is not content: a
    reading that gives "is" no predication of its own has absorbed it into the adjective, which is how the grammar writes it."""
    said = [_content_chars(readings[j]) for j in cands]
    mine = {p for ep in readings[i].eps if ep.cfrom >= 0 and ep.pred != "unknown" for p in range(ep.cfrom, ep.cto)}
    gone = sorted(p for p in set().union(*said) - mine if 2 * sum(p in s for s in said) > len(said))
    return sum(1 for n, p in enumerate(gone) if n == 0 or p - gone[n - 1] > 1)


def _content_chars(r: Reading) -> set[int]:
    return {p for ep in r.eps if ep.cfrom >= 0 and ep.pred.startswith("_") and "RSTR" not in ep.args
            and not copula.is_copula(ep) for p in range(ep.cfrom, ep.cto)}

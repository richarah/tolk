"""tolk reads English statements and questions, keeps what they say with its source, and answers with proofs.

The public interface is read, printed, Mind, and the logical form types. Everything else is internal."""

from tolk import lf as _lf, reading as _reading, words as _words
from tolk.lf import Ask, Atom, Const, Describe, Refusal, Rule, Same, Tell, Var
from tolk.lf import LF
from tolk.mind import Mind

__all__ = ["read", "printed", "Mind", "LF", "Tell", "Rule", "Ask", "Same", "Describe", "Refusal", "Atom", "Const", "Var"]


def read(text: str, known_predicates: frozenset = frozenset(), vocabulary: dict[str, str] | None = None) -> LF:
    """Parse, compile and choose a reading of one sentence. known_predicates, bare names or (name, arity) pairs, steer the choice
    between readings the way a store's predicates would. vocabulary maps a word the grammar may not know to its class, "n", "v" or "a"
    (a database schema's table names, say); it is given to the parser as tagged input. Nothing is stored; no pronoun or definite can be
    resolved without a store."""
    bad = {c for c in (vocabulary or {}).values() if c not in ("n", "v", "a")}
    if bad:
        raise ValueError(f"a vocabulary class is n, v or a, not {sorted(bad)}")
    tags = _words.tags_of(list((vocabulary or {}).items()), text)
    return _reading.read(set(known_predicates), tags, text)[2]


def printed(x: LF) -> str:
    return _lf.show(x)

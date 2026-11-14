"""tolk reads English statements and questions, keeps what they say with its source, and answers with proofs.

The public interface is read, printed, Mind, and the logical form types. Everything else is internal."""

from tolk import compile as _compile, erg as _erg, lf as _lf, sem as _sem
from tolk.lf import Ask, Atom, Const, Describe, Refusal, Rule, Same, Tell, Var
from tolk.lf import LF
from tolk.mind import Mind

__all__ = ["read", "printed", "Mind", "LF", "Tell", "Rule", "Ask", "Same", "Describe", "Refusal", "Atom", "Const", "Var"]


def read(text: str, known_predicates: frozenset = frozenset()) -> LF:
    """Parse, compile and choose a reading of one sentence. known_predicates, bare names or (name, arity) pairs, steer the choice
    between readings the way a store's predicates would. Nothing is stored; no pronoun or definite can be resolved without a store."""
    readings = [_sem.read(raw) for raw in _erg.parse(text)]
    return _compile.choose(readings, set(known_predicates))[1]


def printed(x: LF) -> str:
    return _lf.show(x)

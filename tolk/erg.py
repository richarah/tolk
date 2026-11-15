import re
from pathlib import Path
from typing import NamedTuple

from delphin import ace, derivation

ROOT = Path(__file__).resolve().parent.parent
ACE = ROOT / "erg" / "ace"
GRAMMAR = ROOT / "erg" / "erg-2018.dat"

_session: ace.ACEParser | None = None


def _open() -> ace.ACEParser:
    global _session
    if _session is None:
        _session = ace.ACEParser(str(GRAMMAR), executable=str(ACE), cmdargs=["-n", "5"])
        _session.__enter__()
    return _session


class Parsed(NamedTuple):
    mrs: str
    lex: tuple[tuple[str, int, int], ...]  # the lexical entry the grammar used for each token, with the token's characters


_SPAN = re.compile(r'\+FROM \\"(\d+)\\" \+TO \\"(\d+)\\"')


def lexical_entries(udf: str) -> tuple[tuple[str, int, int], ...]:
    """(entry, from, to) per token of a derivation. An entry the grammar guessed for a word it does not know is named generic_*."""
    found = []

    def walk(node) -> None:
        for d in node.daughters:
            if isinstance(d, derivation.UDFTerminal):
                m = _SPAN.search(d.tokens[0].tfs)
                found.append((node.entity, int(m.group(1)), int(m.group(2))))
            else:
                walk(d)

    walk(derivation.from_string(udf))
    return tuple(found)


def parse(text: str) -> list[Parsed]:
    """One per reading, in parser order."""
    result = _open().interact(text)
    return [Parsed(r["mrs"], lexical_entries(r["derivation"])) for r in result.get("results", [])]


def close() -> None:
    global _session
    if _session is not None:
        _session.__exit__(None, None, None)
        _session = None

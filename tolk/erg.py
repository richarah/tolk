import re
from pathlib import Path
from typing import NamedTuple

from delphin import ace, derivation

ROOT = Path(__file__).resolve().parent.parent
ACE = ROOT / "erg" / "ace"
GRAMMAR = ROOT / "erg" / "erg-2018.dat"

_session: ace.ACEParser | None = None
_tagged: ace.ACEParser | None = None


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
    """(entry, from, to) per token of a derivation. An entry the grammar guessed for a word it lacks is named generic_*."""
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


_TOKEN = re.compile(r"\w+(?:-\w+)*|[^\w\s]")


def tokens(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in _TOKEN.finditer(text)]


def _yy(text: str, tags: dict[str, tuple[str, ...]]) -> str:
    """The sentence as tokens in ACE's YY input. A token named in tags gets those part-of-speech tags; any other capitalised token is a
    proper noun, as the parser's own tokenizer would have it."""
    out = []
    for n, (word, start, end) in enumerate(tokens(text), 1):
        given = tags.get(word.lower()) or (("NNP",) if word[0].isupper() else ())
        tail = ", " + " ".join(f'"{t}" 1.0' for t in given) if given else ""
        out.append(f'({n}, {n - 1}, {n}, <{start}:{end}>, 1, "{word}", 0, "null"{tail})')
    return " ".join(out)


def parse(text: str, tags: dict[str, tuple[str, ...]] | None = None) -> list[Parsed]:
    """One per reading, in parser order. With tags (lowercase token to part-of-speech tags) the sentence is given to the parser
    already tokenised, with those tags: the parser's -y input. Without them the parser tokenizes and tags it itself."""
    result = (_open_tagged().interact(_yy(text, tags)) if tags else _open().interact(text))
    return [Parsed(r["mrs"], lexical_entries(r["derivation"])) for r in result.get("results", [])]


def _open_tagged() -> ace.ACEParser:
    global _tagged
    if _tagged is None:
        _tagged = ace.ACEParser(str(GRAMMAR), executable=str(ACE), cmdargs=["-n", "5", "-y"])
        _tagged.__enter__()
    return _tagged


def close() -> None:
    global _session, _tagged
    for session in (_session, _tagged):
        if session is not None:
            session.__exit__(None, None, None)
    _session = _tagged = None

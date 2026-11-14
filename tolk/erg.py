import os
from pathlib import Path

from delphin import ace

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


def parse(text: str) -> list[str]:
    """SimpleMRS strings, one per reading, in parser order."""
    result = _open().interact(text)
    return [r["mrs"] for r in result.get("results", [])]


def close() -> None:
    global _session
    if _session is not None:
        _session.__exit__(None, None, None)
        _session = None

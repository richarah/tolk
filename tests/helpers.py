import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def sentences(path: Path | None = None) -> list[str]:
    lines = (path or ROOT / "tests" / "sentences.txt").read_text().splitlines()
    return [line for line in lines if line.strip() and not line.startswith("#")]


def fixture_path(text: str) -> Path:
    return FIXTURES / (re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") + ".json")



def readings_of(text: str) -> list:
    """The recorded readings of a sentence, with the lexical entries the parser's derivation gave each."""
    from tolk import sem
    return [sem.read(r["simplemrs"], r["lexical"]) for r in json.loads(fixture_path(text).read_text())["readings"]]

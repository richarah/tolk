import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def sentences() -> list[str]:
    lines = (ROOT / "tests" / "sentences.txt").read_text().splitlines()
    return [line for line in lines if line.strip() and not line.startswith("#")]


def fixture_path(text: str) -> Path:
    return FIXTURES / (re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") + ".json")

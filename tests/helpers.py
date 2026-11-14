import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def sentences() -> list[str]:
    lines = (ROOT / "tests" / "sentences.txt").read_text().splitlines()
    return [line for line in lines if line.strip() and not line.startswith("#")]


def fixture_path(text: str) -> Path:
    return FIXTURES / (re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") + ".json")


def tell_text(db, text: str) -> None:
    """Parse one sentence, choose its reading, and store it. Replaced by Mind.tell in phase 3."""
    from tolk import compile as comp
    from tolk import erg, lf, sem, store

    readings = [sem.read(raw) for raw in erg.parse(text)]
    _, x = comp.choose(readings, store.known_preds(db))
    if isinstance(x, lf.Refusal):
        raise ValueError(lf.show(x))
    sid = store.add_sentence(db, text)
    if isinstance(x, lf.Tell):
        store.tell(db, x, sid)
    elif isinstance(x, lf.Rule):
        store.add_rule(db, x, sid)
    else:
        raise ValueError(lf.show(x))

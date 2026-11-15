"""How many sentences compile, and why the rest are refused.

Usage: coverage.py [extra sentence files...]. The default set is tests/sentences.txt.
Each sentence needs a fixture; run scripts/record.py on the same files first.
"""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from helpers import fixture_path, sentences  # noqa: E402
from tolk import compile as comp  # noqa: E402
from tolk import lf, sem, store  # noqa: E402


def main(files: list[Path]) -> None:
    db = store.open_store()
    total = 0
    compiled = 0
    refusals: Counter[tuple[str, str]] = Counter()
    for f in files:
        for text in sentences(f):
            total += 1
            record = json.loads(fixture_path(text).read_text())
            readings = [sem.read(r["simplemrs"], r["lexical"]) for r in record["readings"]]
            _, x = comp.choose(readings, set(), lambda pred: store.things_with(db, pred))
            if isinstance(x, lf.Refusal):
                refusals[(x.code, x.detail)] += 1
            else:
                compiled += 1
    print(f"compiled {compiled} of {total} ({100 * compiled / total:.1f}%)")
    for (code, detail), n in refusals.most_common():
        print(f"{n:4d}  {code}  {detail}")


if __name__ == "__main__":
    main([Path(a) for a in sys.argv[1:]] or [ROOT / "tests" / "sentences.txt"])

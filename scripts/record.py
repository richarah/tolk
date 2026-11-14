"""Parse each line of tests/sentences.txt and write one fixture per sentence.

Fixtures are the only source of parser output the tests may use. Existing
fixtures are kept unless --force is given.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from helpers import FIXTURES, fixture_path, sentences  # noqa: E402
from tolk import erg, sem  # noqa: E402


def main(force: bool) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for line in sentences():
        out = fixture_path(line)
        if out.exists() and not force:
            continue
        raws = erg.parse(line)
        record = {
            "text": line,
            "readings": [{"simplemrs": raw, "neutral": sem.to_dict(sem.read(raw))} for raw in raws],
        }
        out.write_text(json.dumps(record, indent=2) + "\n")
        print(f"{len(raws)} reading(s): {line}")
    erg.close()


if __name__ == "__main__":
    main(force="--force" in sys.argv)

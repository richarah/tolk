"""Parse each sentence in the given files (default tests/sentences.txt) and write one fixture per sentence.

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


def main(files: list[Path], force: bool) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for line in [s for f in files for s in sentences(f)]:
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
    args = [a for a in sys.argv[1:] if a != "--force"]
    main([Path(a) for a in args] or [ROOT / "tests" / "sentences.txt"], force="--force" in sys.argv)

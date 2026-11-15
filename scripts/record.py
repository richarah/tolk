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


def tagged(path: Path, force: bool) -> None:
    """Lines of `sentence | word=TAG,TAG ...`: parse each in the parser's tagged (-y) mode and record it in tests/fixtures/tagged/."""
    out_dir = FIXTURES / "tagged"
    out_dir.mkdir(parents=True, exist_ok=True)
    for line in sentences(path):
        text, _, spec = line.partition(" | ")
        tags = {w: tuple(t.split(",")) for w, t in (item.split("=") for item in spec.split())}
        out = out_dir / fixture_path(text).name
        if out.exists() and not force:
            continue
        parsed = erg.parse(text, tags)
        record = {"text": text, "tags": {w: list(t) for w, t in tags.items()},
                  "readings": [{"simplemrs": p.mrs, "neutral": sem.to_dict(sem.read(p.mrs)), "lexical": [list(e) for e in p.lex]} for p in parsed]}
        out.write_text(json.dumps(record, indent=2) + "\n")
        print(f"{len(parsed)} tagged reading(s): {line}")
    erg.close()


def main(files: list[Path], force: bool) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for line in [s for f in files for s in sentences(f)]:
        out = fixture_path(line)
        if out.exists() and not force:
            continue
        parsed = erg.parse(line)
        record = {
            "text": line,
            "readings": [{"simplemrs": p.mrs, "neutral": sem.to_dict(sem.read(p.mrs)), "lexical": [list(e) for e in p.lex]} for p in parsed],
        }
        out.write_text(json.dumps(record, indent=2) + "\n")
        print(f"{len(parsed)} reading(s): {line}")
    erg.close()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a not in ("--force", "--tagged")]
    if "--tagged" in sys.argv:
        tagged(Path(args[0]), "--force" in sys.argv)
        sys.exit(0)
    main([Path(a) for a in args] or [ROOT / "tests" / "sentences.txt"], force="--force" in sys.argv)

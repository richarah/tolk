"""Read sentences from standard input, one per line; print the reading, its printed form and the result."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tolk import erg  # noqa: E402
from tolk.mind import Mind  # noqa: E402


def main() -> None:
    mind = Mind()
    for line in sys.stdin:
        text = line.strip()
        if not text:
            continue
        r = mind.hear(text)
        print(f"{text}\n  reading {r.reading} of {r.of}\n  {r.printed}\n  {r.outcome}", flush=True)
    erg.close()


if __name__ == "__main__":
    main()

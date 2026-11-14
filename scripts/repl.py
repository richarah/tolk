"""Read sentences from standard input, one per line; print the reading, its printed form and the result."""

import os
import sys
import traceback
from pathlib import Path
from typing import Iterable, TextIO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tolk import erg  # noqa: E402
from tolk.mind import Mind  # noqa: E402


def run(lines: Iterable[str], mind: Mind, out: TextIO, err: TextIO) -> None:
    for line in lines:
        text = line.strip()
        if not text:
            continue
        try:
            r = mind.hear(text)
        except Exception:  # a bug in tolk must not end the session; it is reported in full, never swallowed
            print(f"{text}\n  internal error, see stderr; continuing", file=out, flush=True)
            print(f"internal error on {text!r}\n{traceback.format_exc()}", file=err, flush=True)
            continue
        print(f"{text}\n  reading {r.reading} of {r.of}\n  {r.printed}\n  {r.outcome}", file=out, flush=True)


def main() -> None:
    # The repl is the only place that reads the environment. TOLK_POLICY is a comma-separated list from specific, trusted, recent.
    policy = tuple(p for p in os.environ.get("TOLK_POLICY", "specific").split(",") if p)
    run(sys.stdin, Mind(policy=policy), sys.stdout, sys.stderr)
    erg.close()


if __name__ == "__main__":
    main()

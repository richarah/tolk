"""The reading-choice table: every sentence in the suite whose chosen reading is not the parser's first, or where a refusal passed a
tie to the next reading. Built from the recorded fixtures and from the stores the dialogue tests chose in.

  choice_table.py --record   run the test suite and record each (sentence, known predicates) the dialogues chose with
  choice_table.py            rebuild tests/choice_table.json and print it as a table
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from helpers import fixture_path, readings_of, sentences  # noqa: E402
from tolk import choice, compile as comp, lf  # noqa: E402

CONTEXTS = ROOT / "tests" / "choice_contexts.json"
TABLE = ROOT / "tests" / "choice_table.json"
TEST_FILES = ("sentences.txt", "extra.txt", "round1.txt", "round2.txt", "own.txt", "generalise.txt", "negation.txt", "choice.txt")


class Recorder:
    """A pytest plugin that notes the text and the known predicates of each choice the dialogues make. It replaces nothing."""

    def __init__(self) -> None:
        self.seen: set[tuple[str, tuple]] = set()
        self.text = None

    def pytest_sessionstart(self, session) -> None:
        from tolk import erg
        parse, preferred = erg.parse, choice.preferred

        def noting_parse(text):
            self.text = text
            return parse(text)

        def noting_preferred(readings, known):
            if self.text is not None:
                self.seen.add((self.text, tuple(sorted((p if isinstance(p, tuple) else (p, -1)) for p in known))))
            self.text = None
            return preferred(readings, known)

        erg.parse, choice.preferred = noting_parse, noting_preferred


def record() -> None:
    import pytest

    plugin = Recorder()
    pytest.main(["-q", "-x", str(ROOT / "tests")], plugins=[plugin])
    CONTEXTS.write_text(json.dumps(sorted([t, [list(p) for p in k]] for t, k in plugin.seen), indent=1) + "\n")
    print(f"{len(plugin.seen)} contexts")


def contexts() -> list[tuple[str, set]]:
    """Every fixture with an empty store, and every store a dialogue chose in."""
    found = {(t, ()) for f in TEST_FILES for t in sentences(ROOT / "tests" / f)}
    found |= {(t, tuple(tuple(p) for p in k)) for t, k in json.loads(CONTEXTS.read_text())}
    return [(t, {tuple(p) for p in k}) for t, k in sorted(found)]


def status(x: lf.LF) -> str:
    return x.code if isinstance(x, lf.Refusal) else type(x).__name__


def row(text: str, known: set) -> dict | None:
    readings = readings_of(text)
    if not readings:
        return None
    chosen, outcome = comp.choose(readings, known)
    cands = choice.candidates(readings)
    tied = choice.preferred(readings, known)
    skipped = [i for i in tied if i < chosen]
    if chosen == 0 and not skipped:
        return None
    return {
        "text": text,
        "known": sorted([list(p) for p in known]),
        "chosen": chosen + 1,
        "decided_by": "refusal passed the tie" if skipped else "criteria",
        "outcome": status(outcome),
        "readings": [
            {"rank": i + 1, **(dict(zip(("generic", "overlap", "swallowed"), choice.measures(readings, i, known))) if i in cands else {}),
             "status": status(comp.compile_reading(r)) if i in cands else "cannot be read"}
            for i, r in enumerate(readings)
        ],
    }


def build() -> list[dict]:
    rows = [r for t, k in contexts() if fixture_path(t).exists() and (r := row(t, k))]
    return sorted(rows, key=lambda r: (r["text"], r["known"]))


def show(rows: list[dict]) -> str:
    out = ["| sentence | store | chosen | decided by | reading: rank (generic, overlap, swallowed) status |", "|---|---|---|---|---|"]
    for r in rows:
        cells = "; ".join(
            f"{x['rank']} ({x['generic']}, {x['overlap']}, {x['swallowed']}) {x['status']}" if "generic" in x else f"{x['rank']} {x['status']}"
            for x in r["readings"])
        out.append(f"| {r['text']} | {len(r['known'])} | {r['chosen']} | {r['decided_by']} | {cells} |")
    return "\n".join(out)


def main() -> None:
    if "--record" in sys.argv:
        record()
        return
    rows = build()
    TABLE.write_text(json.dumps(rows, indent=1) + "\n")
    print(show(rows))
    print(f"\n{len(rows)} rows")


if __name__ == "__main__":
    main()

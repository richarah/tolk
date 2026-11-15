"""Item 5: remove each of three reading-refusal codes in turn, rebuild the choice table, and print the rows that change.

Removing a code means the sentence meets what the code would have been checked before: FALLBACK_PARSE and GRAMMAR_ARTIFACT fall to
UNSUPPORTED_PREDICATE, which is final, and DEMONSTRATIVE's check is skipped, so the demonstrative meets the quantifier family."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import choice_table  # noqa: E402
from tolk import compile as comp, lf  # noqa: E402
from tolk.rules import quant  # noqa: E402

BASE = json.loads((ROOT / "tests" / "choice_table.json").read_text())


def without(code: str):
    """Patch the code out; returns the function that puts it back."""
    real, real_quant, real_artifacts = comp.compile_reading, quant.DEMONSTRATIVE, comp.ARTIFACTS
    if code == "DEMONSTRATIVE":
        quant.DEMONSTRATIVE = re.compile(r"(?!)")
    elif code == "GRAMMAR_ARTIFACT":
        comp.ARTIFACTS = set()
    else:
        def patched(r, lookup=None, history=None):
            x = real(r, lookup, history)
            return lf.Refusal("UNSUPPORTED_PREDICATE", "unknown") if isinstance(x, lf.Refusal) and x.code == code else x
        comp.compile_reading = patched

    def restore() -> None:
        comp.compile_reading, quant.DEMONSTRATIVE, comp.ARTIFACTS = real, real_quant, real_artifacts
    return restore


def changed(code: str) -> list[tuple]:
    restore = without(code)
    try:
        rows = choice_table.build()
    finally:
        restore()
    key = lambda r: (r["text"], json.dumps(r["known"]))  # noqa: E731
    old, new = {key(r): r for r in BASE}, {key(r): r for r in rows}
    out = [(r["text"], len(r["known"]), "chosen " + str(old[k]["chosen"]) + " -> " + (str(new[k]["chosen"]) if k in new else "not in table"),
            old[k]["outcome"] + " -> " + (new[k]["outcome"] if k in new else "-")) for k, r in old.items() if new.get(k) != r]
    out += [(r["text"], len(r["known"]), "new row", r["outcome"]) for k, r in new.items() if k not in old]
    return out


if __name__ == "__main__":
    for code in ("FALLBACK_PARSE", "GRAMMAR_ARTIFACT", "DEMONSTRATIVE"):
        rows = changed(code)
        print(f"\n{code}: {len(rows)} row(s) change")
        for r in rows:
            print("  ", *r, sep=" | ")

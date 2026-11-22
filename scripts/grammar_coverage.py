"""Coverage of tolk over a grammar's own test items: how many of the sentences compile to a logical form tolk can use, and which
refusal codes the rest get. The items are the `item` files of the ERG's tsdb gold profiles (delph-in/erg, tsdb/gold/<profile>/item.gz),
joined into one text file with one item per line in the `@`-separated format; field 7 is the sentence.

    python scripts/grammar_coverage.py items.txt [--limit N] [--out summary.json]

A sentence is "compiled" when tolk.read returns a Tell, Ask, Rule, Same, Describe or Every (not a Refusal). Nothing is stored and no
store is given, so definites need a store and count as refusals. The summary is printed and optionally written as JSON."""

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import tolk  # noqa: E402
from tolk import lf  # noqa: E402


def sentences(path: Path) -> list[str]:
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split("@")
        if len(fields) >= 7 and fields[6].strip():
            out.append(fields[6].strip())
    return out


def main(argv: list[str]) -> None:
    path = Path(argv[0])
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    texts = sentences(path)[:limit]
    codes: collections.Counter = collections.Counter()
    compiled = 0
    for text in texts:
        try:
            x = tolk.read(text)
        except Exception as e:  # a crash is a finding: count it apart from a refusal
            codes[f"CRASH {type(e).__name__}"] += 1
            continue
        if isinstance(x, tolk.Refusal):
            codes[x.code] += 1
        else:
            compiled += 1
    total = len(texts)
    summary = {"sentences": total, "compiled": compiled, "percent": round(100 * compiled / total, 1) if total else 0.0,
               "refusals": dict(codes.most_common())}
    print(f"compiled {compiled} of {total} ({summary['percent']}%)")
    for code, n in codes.most_common(25):
        print(f"{n:6d}  {code}")
    if out:
        Path(out).write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])

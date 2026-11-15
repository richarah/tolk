"""Turn recorded fixtures of the basic patterns into skeletons: the parser's own MRS with the predicate and the names replaced by slots.
This is the one permitted way to make a meaning structure that was not recorded directly (SPEC2 phase 24). Writes tolk/skeletons.json."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from helpers import fixture_path, readings_of  # noqa: E402
from tolk import compile as comp, generate, lf  # noqa: E402

# One sentence per pattern; the pattern itself is found from what the sentence compiles to.
# A predicate takes the frame its entry has: some leave an argument unexpressed, some have none, so a pattern has one skeleton for each.
SOURCES = ["Tweety sings.", "Tweety flies.", "Kim likes Sandy.", "Tweety is a robin.", "Tweety is happy.", "Tweety is calm.",
           "Tweety does not sing.", "Pingu does not fly.", "Kim does not like Sandy.", "Tweety is not a robin.", "Tweety is not happy.",
           "Tweety is not calm."]
OUT = ROOT / "tolk" / "skeletons.json"


def skeleton(text: str) -> tuple[str, str]:
    readings = readings_of(text)
    index, x = comp.choose(readings, set())
    assert isinstance(x, lf.Tell), text
    record = json.loads(fixture_path(text).read_text())["readings"][index]
    (atom,) = [a for a in x.atoms if a.pred.startswith("_")]
    names = [t.id for t in atom.args if isinstance(t, lf.Const) and t.kind == "named"]
    mrs = re.sub(r"<\d+:\d+>", "", record["simplemrs"]).replace(atom.pred, "{p}", 1)
    for slot, name in zip("ab", names):
        mrs = mrs.replace(f'CARG: "{name.title()}"', f'CARG: "{{{slot}}}"')
    return generate.pattern(atom.pred, len(names), atom.positive), mrs


def build() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for key, mrs in map(skeleton, SOURCES):
        if mrs not in out.setdefault(key, []):
            out[key].append(mrs)
    return dict(sorted(out.items()))


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=1) + "\n")
    print(f"{len(build())} skeletons")

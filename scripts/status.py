"""The numbers STATUS.md quotes: the refusal codes with their kind, the settings with their defaults, the module sizes, and the test count.

    status.py           print them
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tolk import lf, settings  # noqa: E402


def codes() -> dict[str, str]:
    return dict(sorted(lf.REFUSALS.items()))


def module_sizes() -> tuple[int, int]:
    sizes = [len(p.read_text().splitlines()) for p in (ROOT / "tolk").rglob("*.py")]
    return len(sizes), max(sizes)


def tests_collected() -> str:
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], capture_output=True, text=True, cwd=ROOT).stdout
    return out.strip().splitlines()[-1]


if __name__ == "__main__":
    print(f"{len(codes())} refusal codes:")
    for code, kind in codes().items():
        print(f"  {code}: {kind}")
    print("settings:", {k: (settings.DEFAULT[k], settings.ALLOWED[k]) for k in settings.ALLOWED})
    n, biggest = module_sizes()
    print(f"{n} modules in tolk/, the longest {biggest} lines")
    print(tests_collected())

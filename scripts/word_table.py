"""Item 3: the ten invented words, each told once in the form that fits it, on an empty store. Prints the table PROGRESS.md holds."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tolk import erg  # noqa: E402
from tolk.mind import Mind  # noqa: E402

# word: (sentence, the class expected, written before the first run)
CASES = {
    "blips": ("Tweety blips.", "v"), "frant": ("Tweety is frant.", "a"), "quorl": ("Tweety is a quorl.", "n"),
    "snerk": ("Tweety snerks.", "v"), "drabbles": ("Tweety drabbles.", "v"), "wug": ("Tweety is a wug.", "n"),
    "tove": ("Tweety is a tove.", "n"), "mimsy": ("Tweety is mimsy.", "a"), "plonth": ("Tweety is a plonth.", "n"),
    "greeb": ("Tweety is a greeb.", "n"),
}


def run() -> list[tuple[str, str, str, str, bool]]:
    rows = []
    for word, (text, pos) in CASES.items():
        m = Mind()
        r = m.tell(text)
        stored = [f"{p}({', '.join(args)})" for p, *args in m.db.execute("SELECT pred, a0, a1, a2 FROM fact WHERE pred LIKE ?", (f"%{word[:4]}%",))]
        classes = [(lemma, p) for lemma, p in m.db.execute("SELECT lemma, pos FROM word")]
        refused = r.printed.startswith("refuse UNKNOWN_WORD")
        right = bool(classes) and all(p == pos for _, p in classes) or refused
        # A common word stored as a name: any fact of the sentence whose predicate is the word itself, as a named thing.
        as_name = any(c[0] == "named" for c in m.db.execute("SELECT 'named' FROM fact WHERE a0 LIKE ? OR a1 LIKE ?", (f"{word}%", f"{word}%")))
        rows.append((word, text, "refused UNKNOWN_WORD" if refused else (f"stored as {classes}" if classes else r.outcome.splitlines()[0] + " " + r.printed.replace("\n", " | ")),
                     pos, right and not as_name))
    return rows


if __name__ == "__main__":
    print("| word | sentence | result | expected class | ok |\n|---|---|---|---|---|")
    for w, t, res, pos, ok in run():
        print(f"| {w} | {t} | {res} | {pos} | {'yes' if ok else 'NO'} |")
    erg.close()

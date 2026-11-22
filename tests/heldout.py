"""Held-out check of reading choice: sentences in no file the choice table was built from (tests/choice*.txt, sentences.txt, extra, rounds).
Each case: (told statements, the sentence under test, expected outcome). The expected outcomes were written before the first run.
Outcome: "Yes", "No", "Unknown" for a question; "stored" or "rule" for a statement; "refused" for any refusal.
Run: python tests/heldout.py  (prints one line per case and the count that matched).

Changes made after the first run, all recorded here and in DECISIONS.md "Held-out check":
- "Mia walks in the park." (and "walked") was refused, because "the park" needs a store: a setup error. The told sentence is now "in Paris".
- "Kim saw Lee ..." expected Yes; a present question about a past told fact is Unknown by the tense rule. Expectation corrected to Unknown.
Not changed: "Bo bakes bread." (reading miss: the causative sense), "A penguin is a bird." (existential or generic: expectation kept)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tolk.mind import Mind  # noqa: E402

CASES = [
    (["Kim saw Lee with a telescope."], "Does Kim see Lee?", "Unknown"),  # changed after the first run from Yes: a past told, a present asked (tense rule)
    (["Tom is a cat.", "Tom sleeps."], "Does the cat sleep?", "Yes"),
    ([], "Kim walks.", "stored"),
    (["Kim walks to school."], "Does Kim walk?", "Yes"),
    (["Bo bakes bread."], "Does Bo bake?", "Yes"),
    (["Pip is taller than Ada."], "Is Ada taller than Pip?", "No"),
    (["Every cat is an animal.", "Tom is a cat."], "Is Tom an animal?", "Yes"),
    (["Tom is not a dog."], "Is Tom a dog?", "No"),
    (["Ada likes Lee and Bo."], "Does Ada like Bo?", "Yes"),
    ([], "Ada likes Lee or Bo.", "refused"),
    (["Ada does not like Lee."], "Does Ada like Lee?", "No"),
    (["Rex barks loudly."], "Does Rex bark?", "Yes"),
    ([], "Kim is happy because Lee sings.", "refused"),
    (["Bo is a teacher."], "Is Bo a teacher?", "Yes"),
    (["Lee is an artist."], "Is Lee an artist?", "Yes"),
    (["Mia walked in Paris."], "Did Mia walk?", "Yes"),
    (["Mia walks in Paris."], "Does Mia walk?", "Yes"),
    (["Sam runs fast."], "Does Sam run?", "Yes"),
    (["Pippa has a red ball."], "Does Pippa have a ball?", "Yes"),
    (["Dogs bark.", "Rex is a dog."], "Does Rex bark?", "Yes"),
    (["A penguin is a bird.", "Pingu is a penguin."], "Is Pingu a bird?", "Yes"),
    (["Tom is a cat."], "Is Tom a dog?", "Unknown"),
    (["Sam sleeps."], "Does Sam sleep?", "Yes"),
    ([], "Mo is a plumber.", "stored"),
    ([], "Every plumber is busy.", "rule"),
    (["Every plumber is busy.", "Mo is a plumber."], "Is Mo busy?", "Yes"),
]


class SetupError(AssertionError):
    """A told statement was not stored, so the case would test nothing."""


def outcome_of(told: list[str], text: str) -> str:
    m = Mind()
    for s in told:
        r = m.tell(s)
        if not (r.outcome.startswith(("stored", "rule", "already"))):
            raise SetupError(f"{s!r} was not stored: {r.outcome[:60]}")
    if text.endswith("?"):
        r = m.ask(text)
        return r.answer.value if r.answer is not None else "refused"
    r = m.tell(text)
    if r.outcome.startswith("refused"):
        return "refused"
    if r.outcome.startswith("rule"):
        return "rule"
    if r.outcome.startswith("stored"):
        return "stored"
    return r.outcome


def run() -> tuple[int, list]:
    misses = []
    for told, text, expected in CASES:
        try:
            got = outcome_of(told, text)
        except SetupError as e:
            misses.append((told, text, expected, f"SETUP: {e}"))
            continue
        if got != expected:
            misses.append((told, text, expected, got))
    return len(CASES) - len(misses), misses


if __name__ == "__main__":
    ok, misses = run()
    for told, text, expected, got in misses:
        print(f"MISS {text!r} told={told} expected {expected} got {got}")
    print(f"{ok} of {len(CASES)} matched")

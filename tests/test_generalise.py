"""The tier constructions again, with other words and names. Written after the review, from the tiers' shapes and not from the code's output.

Each step is (sentence, what the first line of the outcome must be)."""

import pytest

from tolk.mind import Mind

TIER_A = [
    ("Rio is a sparrow.", "stored"), ("Every sparrow is a finch.", "rule stored"), ("Every finch swims.", "rule stored"),
    ("Finches are creatures.", "rule stored"), ("Rio hums.", "stored"), ("Every sparrow that hums is cheerful.", "rule stored"),
    ("Ada is a teacher.", "stored"), ("Ada keeps a cat.", "stored"), ("Every teacher who keeps a cat is calm.", "rule stored"),
    ("Ada admires Bo.", "stored"), ("Tom is a cat.", "stored"), ("Every cat has a master.", "rule stored"),
    ("Does Rio swim?", "Yes"), ("Is Rio a creature?", "Yes"), ("Is Rio cheerful?", "Yes"), ("What swims?", "Rio"),
    ("Which sparrow hums?", "Rio"), ("Who is calm?", "Ada"), ("Who admires Bo?", "Ada"), ("Who does Ada admire?", "Bo"),
    ("Is Bo calm?", "Unknown"), ("Does Tom have a master?", "Yes"),
]
TIER_B = [
    ("Pip is a puffin.", "stored"), ("Pip does not swim.", "stored"), ("Does Pip swim?", "No"),
    ("No puffin swims.", "rule stored"), ("Every puffin is a finch.", "rule stored"), ("Does Pip swim?", "Conflict"),
    ("Bruce Wayne is Batman.", "one thing"), ("Batman swims.", "stored"), ("Does Bruce Wayne swim?", "Yes"),
    ("Is the sparrow cheerful?", "Yes"), ("The cat purrs.", "refused"), ("Rio does not swim.", "refused"),
]
TIER_C = [
    ("Ann sleeps in Rome.", "stored"), ("Bob departed.", "stored"), ("Who sleeps in Rome?", "Ann"),
    ("Where does Ann sleep?", "Rome"), ("Does Ann sleep in Rome?", "Yes"), ("Does Ann sleep in Paris?", "Unknown"),
]
REFUSED = [
    "Most cats purr.", "She swims.", "Rio might swim.", "Rio is smaller than Pip.",
    "If Rio hums, Pip hums.", "Sing!", "Ada wants to sleep.",
    "Every finch that swims quickly is cheerful or calm.",
]


def run(steps: list[tuple[str, str]]) -> None:
    m = Mind()
    for text, want in steps:
        got = m.hear(text).outcome.splitlines()[0]
        assert got.startswith(want), f"{text!r}: wanted {want!r}, got {got!r}"


def test_tier_a_shapes() -> None:
    run(TIER_A)


def test_tier_b_shapes_continue_from_a() -> None:
    run(TIER_A + TIER_B)


def test_tier_c_shapes() -> None:
    run(TIER_C)


@pytest.mark.parametrize("text", REFUSED)
def test_constructions_outside_the_store_are_refused(text: str) -> None:
    assert Mind().hear(text).outcome.startswith("refused")

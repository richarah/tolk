"""Every refusal code is classified once, in lf.REFUSALS, and every final code has the sentence that motivated it."""

import re
from pathlib import Path

import pytest

from tolk import compile as comp, lf
from tolk.mind import Mind

ROOT = Path(__file__).resolve().parent.parent

# code -> (sentences told first, the sentence that is refused with that code)
FINAL = {
    "COORDINATION": ([], "Kim sings and dances."),
    "DEFINITE_MATCHES": ([], "The dog barks."),
    "IDENTITY_NOT_YET": ([], "Every robin is Tweety."),
    "NEGATED_QUESTION": ([], "Does Kim not like Nemo?"),
    "NO_EVENT_READING": ([], "Kim"),
    "SCOPE_AMBIGUOUS": ([], "Every dog does not bark."),
    "UNCONSTRAINED_WANTED": ([], "Who is Kim?"),
    "UNIVERSAL_QUESTION": ([], "Is every dog a mammal?"),
    "UNKNOWN_WORD": ([], "Pip is a blorp."),
    "UNSUPPORTED_ASPECT": ([], "Kim is singing."),
    "UNSUPPORTED_FORCE": ([], "Sing!"),
    "UNSUPPORTED_PREDICATE": ([], "She swims."),
    "UNSUPPORTED_QUANTIFIER": ([], "Most cats purr."),
    "UNSUPPORTED_TENSE": ([], "Kim will sing."),
}


def codes_in_source() -> set[str]:
    text = "".join(p.read_text() for p in (ROOT / "tolk").rglob("*.py"))
    return set(re.findall(r'Refusal\("([A-Z_]+)"', text))


def test_every_code_in_the_source_is_classified() -> None:
    assert codes_in_source() <= set(lf.REFUSALS)


def test_every_classified_code_is_used() -> None:
    assert set(lf.REFUSALS) <= codes_in_source()


@pytest.mark.parametrize("code", FINAL)
def test_final_code_has_its_sentence(code: str) -> None:
    told, text = FINAL[code]
    assert lf.REFUSALS[code] == "final"
    m = Mind()
    for s in told:
        m.tell(s)
    r = m.hear(text)
    assert r.outcome == "refused" and f"refuse {code}:" in r.printed


def test_the_rest_of_the_final_codes_are_tested_where_they_arise() -> None:
    # Store and engine codes need no sentence of their own here: CONTRADICTS is tested in test_dialogue_b (Tweety does not fly),
    # UNSAFE_NEGATION and UNSTRATIFIED in test_dialogue_b on rules, DEFINITE_NEEDS_STORE below.
    assert {c for c, k in lf.REFUSALS.items() if k == "final"} - set(FINAL) == {
        "CONTRADICTS", "DEFINITE_NEEDS_STORE", "UNSAFE_NEGATION", "UNSTRATIFIED"}


def test_a_definite_without_a_store_needs_one() -> None:
    import json
    from helpers import fixture_path
    from tolk import sem
    raw = json.loads(fixture_path("The dog barks.").read_text())["readings"][0]["simplemrs"]
    assert comp.compile_reading(sem.read(raw)) == lf.Refusal("DEFINITE_NEEDS_STORE", "_the_q")

"""Every refusal code is classified once, in lf.REFUSALS, and every final code has the sentence that motivated it."""

import re
from pathlib import Path

import pytest

from tolk import compile as comp, lf
from tolk.mind import Mind

ROOT = Path(__file__).resolve().parent.parent

# code -> (sentences told first, the sentence that is refused with that code)
FINAL = {
    "COORDINATION": ([], "Kim sings or dances."),
    "DEFINITE_MATCHES": ([], "The dog barks."),
    "IDENTITY_NOT_YET": ([], "Every robin is Tweety."),
    "NEGATED_INDEFINITE": ([], "If Kim does not own a dog, Kim is happy."),
    "NO_EVENT_READING": ([], "Kim"),
    "SCOPE_AMBIGUOUS": ([], "Every dog does not bark."),
    "UNIVERSAL_QUESTION": ([], "Who likes every dog?"),
    "UNKNOWN_WORD": ([], "Tweety flibbered."),  # was "Does Pip glorb?", which phase 16 audit (2B) now answers: a past tense is the class the parser cannot be given
    "UNSUPPORTED_ASPECT": ([], "Kim is singing."),
    "UNSUPPORTED_FORCE": ([], "Sing!"),
    "UNSUPPORTED_PREDICATE": ([], "Kim can sing."),
    "NO_ANTECEDENT": ([], "She swims."),
    "AMBIGUOUS_PRONOUN": (["Kim likes Sandy."], "She is happy."),
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
    # UNSAFE_NEGATION and NEGATION_CYCLE in test_dialogue_b on rules, DEFINITE_NEEDS_STORE below.
    assert {c for c, k in lf.REFUSALS.items() if k == "final"} - set(FINAL) == {
        "CONTRADICTS", "DEFINITE_NEEDS_STORE", "UNSAFE_NEGATION", "NEGATION_CYCLE"}


def test_a_definite_without_a_store_needs_one() -> None:
    import json
    from helpers import fixture_path
    from tolk import sem
    raw = json.loads(fixture_path("The dog barks.").read_text())["readings"][0]["simplemrs"]
    assert comp.compile_reading(sem.read(raw)) == lf.Refusal("DEFINITE_NEEDS_STORE", "_the_q")


def test_unconstrained_wanted_is_a_reading_refusal_so_who_is_a_bird_is_answered() -> None:
    # Reading 1 of "Who is a bird?" has nothing to enumerate; reading 2 is the question. A final code would stop at reading 1.
    assert lf.REFUSALS["UNCONSTRAINED_WANTED"] == "reading"
    m = Mind()
    m.tell("Tweety is a bird.")
    assert m.ask("Who is a bird?").outcome.splitlines()[0] == "Tweety"
    r = m.hear("Who is who?")
    assert r.outcome == "refused" and "UNCONSTRAINED_WANTED" in r.printed

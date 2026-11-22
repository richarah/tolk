"""Phase 21: beliefs and reports. The dialogue is SPEC2's; the rest use other words. Expectations were written before the code."""

import pytest

from tolk.ask import UNKNOWN, YES
from tolk.mind import Mind


@pytest.fixture()
def mind() -> Mind:
    return Mind()


def first(m: Mind, text: str) -> str:
    return m.hear(text).outcome.splitlines()[0]


def test_the_dialogue(mind: Mind) -> None:
    mind.tell("Kim believes that Tweety swims.")
    assert first(mind, "Does Tweety swim?") == "Unknown"
    assert first(mind, "Does Kim believe that Tweety swims?") == "Yes"
    assert first(mind, "Does Sandy believe that Tweety swims?") == "Unknown"


def test_who_and_what(mind: Mind) -> None:
    mind.tell("Kim believes that Tweety swims.")
    assert first(mind, "Who believes that Tweety swims?") == "Kim"
    assert first(mind, "What does Kim believe?") == "[swim(tweety)]"


def test_the_content_must_be_exactly_the_same(mind: Mind) -> None:
    mind.tell("Kim believes that Rio flies.")
    assert first(mind, "Does Kim believe that Rio sings?") == "Unknown"
    assert first(mind, "Does Kim believe that Pip flies?") == "Unknown"
    assert first(mind, "Does Kim believe that Rio flies?") == "Yes"


def test_the_verb_must_be_the_same(mind: Mind) -> None:
    mind.tell("Kim believes that Rio flies.")
    mind.tell("Sandy says that Rio flies.")
    assert first(mind, "Who believes that Rio flies?") == "Kim"
    assert first(mind, "Who says that Rio flies?") == "Sandy"


def test_knowing_does_not_make_the_content_true(mind: Mind) -> None:
    mind.tell("Kim knows that Rio flies.")
    assert first(mind, "Does Rio fly?") == "Unknown"
    assert first(mind, "Does Kim know that Rio flies?") == "Yes"


def test_a_person_can_hold_two_claims(mind: Mind) -> None:
    mind.tell("Kim believes that Rio flies.")
    mind.tell("Kim believes that Rio sings.")
    lines = mind.hear("What does Kim believe?").outcome.splitlines()[0]
    assert "fly(rio)" in lines and "sing(rio)" in lines


def test_nothing_is_derived_inside_a_claim(mind: Mind) -> None:
    for s in ["Every bird flies.", "Pip is a bird.", "Kim believes that Pip is a bird."]:
        mind.tell(s)
    assert first(mind, "Does Pip fly?") == "Yes"
    assert first(mind, "Does Kim believe that Pip flies?") == "Unknown"
    assert mind.db.execute("SELECT COUNT(*) FROM fact WHERE ctx NOT IN ('world') AND pred = '_fly_v_1'").fetchone()[0] == 0


def test_a_claim_does_not_reach_the_world(mind: Mind) -> None:
    mind.tell("Kim believes that Rio is a sparrow.")
    assert first(mind, "Is Rio a sparrow?") == "Unknown"
    assert first(mind, "Who is a sparrow?") == "Unknown"
    assert mind.ask("Who is Rio?").outcome == "Unknown"


def test_a_claim_inside_a_claim_is_refused(mind: Mind) -> None:
    assert mind.hear("Sandy says that Kim believes that Rio flies.").outcome == "refused"


def test_an_infinitive_with_another_subject_is_not_a_claim(mind: Mind) -> None:
    # Subject control ("Kim wants to sleep.") is a claim now (tests/test_control.py); object control is refused.
    assert mind.hear("Lee wants Kim to sleep.").outcome == "refused"


def test_the_same_claim_told_twice_is_a_repeat(mind: Mind) -> None:
    mind.tell("Kim believes that Rio flies.")
    assert mind.tell("Kim believes that Rio flies.").outcome.startswith("already told")
    assert mind.db.execute("SELECT COUNT(*) FROM claim").fetchone()[0] == 1


def test_forgetting_a_report_removes_its_claim(mind: Mind) -> None:
    mind.tell("Kim believes that Rio flies.")
    assert mind.tell("Forget that Kim believes that Rio flies.").outcome.startswith("forgot")
    assert first(mind, "Does Kim believe that Rio flies?") == "Unknown"
    assert mind.db.execute("SELECT COUNT(*) FROM claim").fetchone()[0] == 0


def test_a_claim_in_a_supposition_is_refused(mind: Mind) -> None:
    assert mind.suppose("Kim believes that Rio flies.").outcome.startswith("refused")
    mind.drop()


def test_the_report_itself_has_a_tense(mind: Mind) -> None:
    mind.tell("Kim believed that Rio flies.")
    assert first(mind, "Did Kim believe that Rio flies?") == "Yes"
    assert first(mind, "Does Kim believe that Rio flies?") == "Unknown"


def test_describe_shows_the_claim_a_person_holds(mind: Mind) -> None:
    mind.tell("Kim believes that Rio flies.")
    assert "believe(kim, [fly(rio)])" in mind.hear("Who is Kim?").outcome

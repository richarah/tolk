"""Phase 10: Who is X? and What is X? describe a known thing. Expectations were written before the code."""

import pytest

from tolk import lf
from tolk.lf import Const
from tolk.mind import Mind


@pytest.fixture(scope="module")
def mind() -> Mind:
    m = Mind()
    for s in ["Rio is a sparrow.", "Rio sings.", "Every sparrow is a bird.", "Ada owns a cat.", "Ada does not like Bo."]:
        m.tell(s)
    return m


def test_the_logical_form_is_describe(mind: Mind) -> None:
    assert mind.hear("Who is Rio?").printed == "describe rio"


def test_told_facts_come_before_derived_ones(mind: Mind) -> None:
    lines = mind.hear("Who is Rio?").outcome.splitlines()
    told = [i for i, l in enumerate(lines) if "(told:" in l]
    derived = [i for i, l in enumerate(lines) if "(by rule" in l]
    assert len(told) == 2 and len(derived) == 1 and max(told) < min(derived)
    assert any(l.startswith("Rio is a sparrow") for l in lines) and any("Rio is a bird" in l for l in lines)


def test_what_is_and_who_is_say_the_same(mind: Mind) -> None:
    assert mind.hear("What is Rio?").outcome == mind.hear("Who is Rio?").outcome


def test_a_negative_fact_and_an_event_modifier_belong_to_the_description(mind: Mind) -> None:
    out = mind.hear("What is Ada?").outcome
    assert "Ada doesn't like Bo." in out and "own(ada, a1)" in out and "a1 is a cat" not in out


def test_a_name_that_only_appears_in_a_negative_fact_is_known(mind: Mind) -> None:
    assert "Ada doesn't like Bo." in mind.hear("Who is Bo?").outcome


def test_an_unknown_name_is_unknown(mind: Mind) -> None:
    assert mind.hear("Who is Zed?").outcome == "Unknown"


def test_describe_survives_a_merge(mind: Mind) -> None:
    m = Mind()
    m.tell("Clark Kent is Superman.")
    m.tell("Superman flies.")
    assert "fly(superman)" in m.hear("Who is Clark Kent?").outcome or "fly(clark_kent)" in m.hear("Who is Clark Kent?").outcome

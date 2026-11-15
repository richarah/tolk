"""Phase 22: comparatives. The dialogue is SPEC2's; the rest use other words. Expectations were written before the code."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


@pytest.fixture()
def mind() -> Mind:
    m = Mind()
    m.tell("Kim is taller than Sandy.")
    m.tell("Sandy is taller than Lee.")
    return m


def test_the_dialogue(mind: Mind) -> None:
    assert mind.ask("Is Kim taller than Lee?").answer.value == YES
    assert mind.ask("Is Lee taller than Kim?").answer.value == NO
    assert mind.ask("Is Kim tall?").answer.value == UNKNOWN
    r = mind.ask("Who is the tallest?")
    assert r.outcome.splitlines()[0] == "Kim (among those I know)"


def test_one_fact_with_a_system_built_predicate(mind: Mind) -> None:
    preds = {p for (p,) in mind.db.execute("SELECT DISTINCT pred FROM fact WHERE level = 1")}
    assert preds == {"comp:_tall_a_1"}


def test_the_transitive_step_is_named_as_a_built_in_axiom(mind: Mind) -> None:
    assert "by built-in axiom: comp:_tall_a_1 is transitive" in mind.ask("Is Kim taller than Lee?").outcome


def test_who_is_taller_than_uses_the_closure(mind: Mind) -> None:
    assert mind.ask("Who is taller than Lee?").outcome.splitlines()[0] == "Kim and Sandy"


def test_each_adjective_has_its_own_comparison() -> None:
    m = Mind()
    m.tell("Ada is older than Bo.")
    m.tell("Bo is older than Cy.")
    assert m.ask("Is Ada older than Cy?").answer.value == YES
    assert m.ask("Is Cy older than Ada?").answer.value == NO
    assert m.ask("Is Ada old?").answer.value == UNKNOWN
    assert m.ask("Who is the oldest?").outcome.splitlines()[0] == "Ada (among those I know)"
    assert m.ask("Is Ada heavier than Bo?").answer.value == UNKNOWN


def test_shorter_is_its_own_adjective_with_no_link_to_taller() -> None:
    m = Mind()
    m.tell("Ada is shorter than Bo.")
    assert m.ask("Is Bo taller than Ada?").answer.value == UNKNOWN
    assert m.ask("Is Bo shorter than Ada?").answer.value == NO


def test_two_chains_with_no_link_give_no_tallest() -> None:
    m = Mind()
    m.tell("Kim is taller than Sandy.")
    m.tell("Bo is taller than Lee.")
    assert m.ask("Who is the tallest?").answer.value == UNKNOWN


def test_nothing_known_gives_no_tallest() -> None:
    assert Mind().ask("Who is the tallest?").answer.value == UNKNOWN


@pytest.mark.parametrize("text", [
    "Kim is as tall as Sandy.", "Kim is less tall than Sandy.", "Kim is two metres taller than Sandy.",
])
def test_equal_less_and_measures_are_refused(text: str) -> None:
    r = Mind().hear(text)
    assert r.outcome == "refused" and "UNSUPPORTED_PREDICATE" in r.printed


def test_a_comparison_in_the_past_is_refused_not_stored_as_present(mind: Mind) -> None:
    r = mind.hear("Kim was taller than Lee.")
    assert r.outcome == "refused" and "UNSUPPORTED_TENSE" in r.printed


def test_the_opposite_order_is_refused_as_a_contradiction(mind: Mind) -> None:
    assert mind.tell("Sandy is taller than Kim.").outcome.startswith("refused, contradicts")


def test_a_negated_comparison_is_a_negative_fact(mind: Mind) -> None:
    assert mind.tell("Lee is not taller than Bo.").outcome.startswith("stored")
    assert mind.ask("Is Lee taller than Bo?").answer.value == NO
    assert mind.ask("Is Bo taller than Lee?").answer.value == UNKNOWN


def test_comparing_with_something_not_named_is_refused() -> None:
    r = Mind().hear("Kim is taller than a cat.")
    assert r.outcome == "refused"

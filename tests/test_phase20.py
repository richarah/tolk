"""Phase 20: time. The dialogue is SPEC2's; the rest use other words. Expectations were written before the code."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


def first(m: Mind, text: str) -> str:
    return m.hear(text).outcome.splitlines()[0]


def test_a_past_fact_answers_a_past_question_only() -> None:
    m = Mind()
    m.tell("Kim lived in Oslo.")
    assert first(m, "Does Kim live in Oslo?") == "Unknown"
    assert first(m, "Did Kim live in Oslo?") == "Yes"


def test_the_tier_c_line_that_changes() -> None:
    m = Mind()
    m.tell("Sandy arrived.")
    assert first(m, "Does Sandy arrive?") == "Unknown"
    assert first(m, "Did Sandy arrive?") == "Yes"


def test_a_present_fact_does_not_answer_a_past_question() -> None:
    m = Mind()
    m.tell("Kim lives in Oslo.")
    assert first(m, "Did Kim live in Oslo?") == "Unknown"
    assert first(m, "Does Kim live in Oslo?") == "Yes"


def test_a_fact_with_no_event_is_tenseless() -> None:
    m = Mind()
    m.tell("Tweety is a robin.")
    assert first(m, "Is Tweety a robin?") == "Yes"
    assert first(m, "Was Tweety a robin?") == "Yes"


def test_a_negative_fact_has_no_event_and_matches_any_tense() -> None:
    m = Mind()
    m.tell("Pingu does not fly.")
    assert first(m, "Does Pingu fly?") == "No"
    assert first(m, "Did Pingu fly?") == "No"


def test_a_derived_event_takes_the_tense_of_the_conclusion() -> None:
    m = Mind()
    m.tell("Every dog barked.")
    m.tell("Rex is a dog.")
    assert first(m, "Did Rex bark?") == "Yes"
    assert first(m, "Does Rex bark?") == "Unknown"
    m2 = Mind()
    m2.tell("Every dog barks.")
    m2.tell("Rex is a dog.")
    assert first(m2, "Does Rex bark?") == "Yes"
    assert first(m2, "Did Rex bark?") == "Unknown"


def test_the_ordering_dialogue() -> None:
    m = Mind()
    m.tell("Kim arrived before Sandy left.")
    m.tell("Sandy left before Lee sang.")
    r = m.ask("Did Kim arrive before Lee sang?")
    assert r.answer.value == YES
    assert "by built-in axiom: before is transitive" in r.outcome
    r = m.ask("Did Lee sing before Kim arrived?")
    assert r.answer.value == NO
    assert "by built-in axiom: before is asymmetric" in r.outcome


def test_after_is_before_the_other_way_round() -> None:
    m = Mind()
    m.tell("Kim arrived after Sandy left.")
    assert m.ask("Did Sandy leave before Kim arrived?").answer.value == YES
    assert m.ask("Did Kim arrive before Sandy left?").answer.value == NO
    assert m.ask("Did Kim arrive after Sandy left?").answer.value == YES


def test_the_year_dialogue() -> None:
    m = Mind()
    m.tell("Kim lived in Oslo in 2019.")
    m.tell("Kim lived in Bergen in 2021.")
    assert first(m, "Where did Kim live in 2019?") == "Oslo"
    assert first(m, "Where did Kim live in 2021?") == "Bergen"
    assert first(m, "Where did Kim live in 2020?") == "Unknown"


def test_an_earlier_year_is_before_a_later_one() -> None:
    m = Mind()
    m.tell("Ada slept in 2019.")
    m.tell("Bo slept in 2021.")
    r = m.ask("Did Ada sleep before Bo slept?")
    assert r.answer.value == YES and "earlier year is before" in r.outcome
    assert m.ask("Did Bo sleep before Ada slept?").answer.value == NO


def test_orderings_and_years_chain() -> None:
    m = Mind()
    m.tell("Ada slept in 2019.")
    m.tell("Bo slept in 2021.")
    m.tell("Bo slept before Cy sang.")
    assert m.ask("Did Ada sleep before Cy sang?").answer.value == YES


def test_a_store_that_never_mentions_time_has_no_axioms() -> None:
    m = Mind()
    m.tell("Tweety is a robin.")
    assert m.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0] == 0


# Future and present perfect are stored since M3 (tests/test_tense.py); progressive and the rest stay refused.
@pytest.mark.parametrize("text", ["Kim will be arriving.", "Kim arrived since 2019.", "Kim arrived until Sandy left.", "Kim had arrived."])
def test_what_stays_refused(text: str) -> None:
    assert Mind().hear(text).outcome == "refused"


def test_two_clauses_with_the_same_content_are_one_event_in_an_ordering() -> None:
    m = Mind()
    m.tell("Kim arrived before Sandy left.")
    m.tell("Sandy left before Lee sang.")
    assert m.db.execute("SELECT COUNT(DISTINCT a0) FROM fact WHERE pred = '_leave_v_1'").fetchone()[0] == 1

"""Sentences from the phase 7 review. Each one was once compiled wrongly; these tests keep the corrected meaning."""

import pytest

from tolk import say
from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


@pytest.fixture()
def mind() -> Mind:
    return Mind()


def test_negated_noun_is_a_negative_fact(mind: Mind) -> None:
    r = mind.tell("Milo is not a cat.")
    assert r.printed == "tell   not _cat_n_1(milo)"


def test_no_negates_the_copula_complement(mind: Mind) -> None:
    r = mind.tell("No teacher is a student.")
    assert r.printed == "rule   not _student_n_of(X) :- _teacher_n_of(X)"


def test_bare_plural_object_is_existential(mind: Mind) -> None:
    r = mind.tell("Ben teaches math.")
    assert r.printed == "tell   _teach_v_1(e1, ben, a1)\ntell   _math_n_1(a1)"


def test_bare_plural_under_universal_is_skolem_per_binding(mind: Mind) -> None:
    r = mind.tell("Every car needs fuel.")
    assert r.printed == "rule   _need_v_1(E!, X, Y!), _fuel_n_1(Y) :- _car_n_1(X)"


def test_adverb_attaches_to_the_event_it_modifies(mind: Mind) -> None:
    r = mind.tell("Every student studies hard.")
    assert r.printed == "rule   _study_v_1(E!, X), _hard_a_for(E) :- _student_n_of(X)"


def test_leo_walks_to_school_keeps_the_school_restriction(mind: Mind) -> None:
    r = mind.tell("Leo walks to school.")
    assert "_school_n_1(a1)" in r.printed


def test_where_finds_a_state_preposition(mind: Mind) -> None:
    mind.tell("Sam works in Paris.")
    r = mind.ask("Where does Sam work?")
    assert say.answer_text(mind.db, r.answer) == "Paris"


def test_definite_resolves_once_its_referent_is_told(mind: Mind) -> None:
    mind.tell("Anna reads a book.")
    r = mind.tell("The book is old.")
    assert r.outcome.startswith("stored")
    assert mind.ask("Is the book old?").answer.value == YES


def test_definite_with_no_referent_is_refused(mind: Mind) -> None:
    r = mind.tell("The cup is empty.")
    assert r.outcome == "refused"
    assert "DEFINITE_MATCHES: 0 known things match" in r.printed


def test_numbers_are_refused(mind: Mind) -> None:
    r = mind.tell("Ana owns two cats.")
    assert r.printed == "refuse UNSUPPORTED_PREDICATE: card"


def test_negated_fact_answers_no_with_a_bare_plural_elsewhere(mind: Mind) -> None:
    mind.tell("Milo is not a cat.")
    assert mind.ask("Is Milo a cat?").answer.value == NO
    assert mind.ask("Is Milo happy?").answer.value == UNKNOWN

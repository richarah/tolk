"""Phase 13: pronouns. The dialogue is SPEC2's; the rest use other words. Expectations were written before the code."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


@pytest.fixture()
def mind() -> Mind:
    return Mind()


def test_the_dialogue(mind: Mind) -> None:
    assert mind.tell("I am a person.").outcome.startswith("stored")
    assert mind.ask("Am I a person?").answer.value == YES
    assert mind.ask("Are you a cat?").answer.value == UNKNOWN
    mind.tell("Tweety is a robin.")
    r = mind.tell("It sings.")
    assert "it = tweety" in r.printed and r.outcome.startswith("stored")
    assert mind.ask("Does Tweety sing?").answer.value == YES
    mind.tell("Kim likes Sandy.")
    r = mind.hear("She is happy.")
    assert r.outcome == "refused" and "AMBIGUOUS_PRONOUN" in r.printed


def test_the_user_is_worded_as_you_and_tolk_as_i(mind: Mind) -> None:
    mind.tell("I am a person.")
    assert "you are a person" in mind.ask("Am I a person?").outcome
    mind.tell("You are a robin.")
    assert "I am a robin" in mind.ask("Are you a robin?").outcome


def test_a_pronoun_with_nothing_before_it_is_refused(mind: Mind) -> None:
    r = mind.hear("It sings.")
    assert r.outcome == "refused" and "NO_ANTECEDENT" in r.printed


def test_the_most_recent_thing_wins_across_sentences(mind: Mind) -> None:
    mind.tell("Rio sings.")
    mind.tell("Pip hums.")
    r = mind.tell("It sings.")
    assert "it = pip" in r.printed
    assert mind.ask("Does Pip sing?").answer.value == YES


def test_two_things_in_the_last_sentence_are_ambiguous(mind: Mind) -> None:
    mind.tell("Ada keeps a cat.")
    assert "AMBIGUOUS_PRONOUN" in mind.hear("It purrs.").printed


def test_a_thing_made_by_an_indefinite_can_be_the_antecedent(mind: Mind) -> None:
    mind.tell("Ada is a teacher.")
    mind.tell("Tom is a cat.")
    r = mind.tell("He sleeps.")
    assert "he = tom" in r.printed


def test_i_and_you_in_one_sentence(mind: Mind) -> None:
    mind.tell("I like Ada.")
    r = mind.ask("Who likes Ada?")
    assert r.outcome.splitlines()[0] == "you"
    assert mind.ask("Does Ada like me?").answer.value == UNKNOWN


def test_a_merged_name_is_followed(mind: Mind) -> None:
    mind.tell("Clark Kent is Superman.")
    mind.tell("He flies.")
    assert mind.ask("Does Clark Kent fly?").answer.value == YES


def test_a_pronoun_in_a_question_and_in_a_conditional(mind: Mind) -> None:
    mind.tell("Rio is a sparrow.")
    mind.tell("Rio sings.")
    assert mind.ask("Does it sing?").answer.value == YES
    assert "rio" in mind.tell("If it hums, Ada is calm.").printed


def test_i_am_happy_and_kim_is_unknown(mind: Mind) -> None:
    mind.tell("I am happy.")
    assert mind.ask("Am I happy?").answer.value == YES
    assert mind.ask("Is Kim happy?").answer.value == UNKNOWN

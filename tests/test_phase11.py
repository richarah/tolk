"""Phase 11: conditionals become rules. Expected forms were written from the fixtures' shapes: the grammar's if-then predication
takes the consequent first and the antecedent second."""

import pytest

from tolk.ask import CONFLICT, NO, UNKNOWN, YES
from tolk.mind import Mind


@pytest.fixture()
def mind() -> Mind:
    return Mind()


def test_if_before_the_clause(mind: Mind) -> None:
    assert mind.tell("If Kim owns a dog, Kim is happy.").printed == "rule   _happy_a_with(E!, kim) :- _own_v_1(E1, kim, X), _dog_n_1(X)"


def test_if_after_the_clause(mind: Mind) -> None:
    assert mind.tell("Tweety flies if Tweety is a bird.").printed == "rule   _fly_v_1(E!, tweety) :- _bird_n_1(tweety)"


def test_an_indefinite_in_the_antecedent_is_a_variable(mind: Mind) -> None:
    assert mind.tell("If a robin sings, Kim is happy.").printed == "rule   _happy_a_with(E!, kim) :- _robin_n_1(X), _sing_v_1(E1, X)"


def test_the_rule_fires_when_its_antecedent_holds(mind: Mind) -> None:
    mind.tell("If Kim owns a dog, Kim is happy.")
    assert mind.ask("Is Kim happy?").answer.value == UNKNOWN
    mind.tell("Kim owns a dog.")
    r = mind.ask("Is Kim happy?")
    assert r.answer.value == YES and "(by rule 1)" in r.outcome


def test_a_ground_rule_with_a_name_fires(mind: Mind) -> None:
    mind.tell("Tweety flies if Tweety is a bird.")
    mind.tell("Tweety is a bird.")
    assert mind.ask("Does Tweety fly?").answer.value == YES
    assert mind.ask("Does Sandy fly?").answer.value == UNKNOWN


def test_a_negated_consequent_gives_a_negative_fact(mind: Mind) -> None:
    mind.tell("If Kim owns a dog, Kim is not happy.")
    mind.tell("Kim owns a dog.")
    assert mind.ask("Is Kim happy?").answer.value == NO


def test_a_negated_antecedent_over_a_thing_is_a_negative_check(mind: Mind) -> None:
    assert mind.tell("If Kim is not a person, Kim is happy.").outcome.startswith("refuse UNSAFE_NEGATION")
    assert mind.tell("If Kim does not own a dog, Kim is happy.").printed.startswith("refuse NEGATED_INDEFINITE")


def test_a_conditional_question_and_a_pronoun_are_refused(mind: Mind) -> None:
    assert mind.hear("If Kim sleeps, is Kim happy?").outcome == "refused"
    assert mind.hear("If it sleeps, Kim is happy.").outcome == "refused"


def test_a_conditional_with_a_past_antecedent_is_refused_not_read_as_present(mind: Mind) -> None:
    assert "UNSUPPORTED_TENSE" in mind.hear("If Kim owned a dog, Kim is happy.").printed


# the same constructions with other words
@pytest.mark.parametrize("rule, fact, question, answer", [
    ("If Ada keeps a cat, Ada is calm.", "Ada keeps a cat.", "Is Ada calm?", YES),
    ("Rio hums if Rio is a sparrow.", "Rio is a sparrow.", "Does Rio hum?", YES),
    ("If a teacher admires Bo, Ada is cheerful.", "Tom is a teacher.", "Is Ada cheerful?", UNKNOWN),
    ("If a teacher admires Bo, Ada is cheerful.", "Ada admires Bo.", "Is Ada cheerful?", UNKNOWN),
    ("Bo is calm if Bo keeps a cat.", "Bo keeps a cat.", "Is Bo calm?", YES),
])
def test_other_words(rule: str, fact: str, question: str, answer: str) -> None:
    m = Mind()
    assert m.tell(rule).outcome == "rule stored"
    m.tell(fact)
    assert m.ask(question).answer.value == answer

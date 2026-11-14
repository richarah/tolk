"""Phase 15: coordination. And distributes; or is accepted only in questions, where either side makes it Yes.
Expectations were written before the code."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


def run(told: list[str], question: str) -> str:
    m = Mind()
    for s in told:
        m.tell(s)
    return m.ask(question).answer.value


def test_and_between_names_stores_two_facts() -> None:
    m = Mind()
    assert m.tell("Kim and Sandy are happy.").outcome == "stored, 2 new fact(s)"
    assert run(["Kim and Sandy are happy."], "Is Sandy happy?") == YES


@pytest.mark.parametrize("told, question, answer", [
    (["Kim and Sandy are happy."], "Is Kim happy?", YES),
    (["Kim and Sandy are happy."], "Is Lee happy?", UNKNOWN),
    (["Kim sings and dances."], "Does Kim dance?", YES),
    (["Kim sings and Sandy dances."], "Does Sandy dance?", YES),
    (["Kim sings and Sandy dances."], "Does Kim dance?", UNKNOWN),
    (["Kim likes Sandy and Lee."], "Does Kim like Lee?", YES),
    (["Ada keeps a cat and a bird."], "Is Ada happy?", UNKNOWN),
    (["Kim sings.", "Sandy sings."], "Do Kim and Sandy sing?", YES),
    (["Kim sings."], "Do Kim and Sandy sing?", UNKNOWN),
    (["Rio hums."], "Does Rio hum or sing?", YES),
    (["Rio hums."], "Does Rio sing or dance?", UNKNOWN),
    (["Kim likes Lee."], "Does Kim like Sandy or Lee?", YES),
    (["Kim likes Lee."], "Does Kim like Sandy or Bo?", UNKNOWN),
    (["Kim owns a dog."], "Does Kim own a cat or a dog?", YES),
    (["Kim owns a dog."], "Does Kim own a cat or a bird?", UNKNOWN),
    (["Pingu does not fly."], "Does Pingu fly or sing?", UNKNOWN),
])
def test_other_words(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer


def test_an_or_question_has_a_proof_from_the_side_that_held() -> None:
    m = Mind()
    m.tell("Kim owns a dog.")
    out = m.ask("Does Kim own a cat or a dog?").outcome
    assert "a1 is a dog" in out and "cat" not in out


def test_who_questions_take_the_union_of_the_sides() -> None:
    m = Mind()
    m.tell("Kim sings.")
    m.tell("Sandy dances.")
    assert m.ask("Who sings or dances?").outcome.splitlines()[0] == "Kim and Sandy"


def test_every_side_no_is_no() -> None:
    m = Mind()
    m.tell("Pingu does not fly.")
    m.tell("Pingu does not sing.")
    assert m.ask("Does Pingu fly or sing?").answer.value == NO


@pytest.mark.parametrize("text", [
    "Kim sings or dances.", "Kim likes Sandy or Lee.", "Kim owns a cat or a dog.", "Every dog barks or sleeps.",
    "Kim sings and Sandy dances or Lee sleeps.",
])
def test_or_in_a_statement_is_refused(text: str) -> None:
    assert "COORDINATION" in Mind().hear(text).printed


def test_a_group_in_a_rule_is_refused_and_nothing_is_stored() -> None:
    m = Mind()
    assert m.hear("Every dog and every cat sleeps.").outcome == "refused"
    assert m.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0] == 0


def test_and_in_a_rule_head_creates_both() -> None:
    m = Mind()
    m.tell("Every dog barks and sleeps.")
    m.tell("Rex is a dog.")
    assert m.ask("Does Rex sleep?").answer.value == YES

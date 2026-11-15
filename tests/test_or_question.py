"""Item 3: "Is Kim happy or Lee happy?" is a question of two clauses with the auxiliary left out of the second. The grammar reads "Lee" there
as a modifier of "happy", so the sentence is read again with the auxiliary written out. Yes if either side is Yes, Unknown if neither is
known; an or in a statement stays refused."""

import pytest

import tolk
from tolk import lf
from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


def run(told: list[str], question: str) -> str:
    m = Mind()
    for s in told:
        m.tell(s)
    return m.ask(question).answer.value


@pytest.mark.parametrize("told, question, answer", [
    (["Kim is happy."], "Is Kim happy or Lee happy?", YES),
    (["Lee is happy."], "Is Kim happy or Lee happy?", YES),
    (["Kim is happy.", "Lee is happy."], "Is Kim happy or Lee happy?", YES),
    (["Sam is happy."], "Is Kim happy or Lee happy?", UNKNOWN),
    ([], "Is Kim happy or Lee happy?", UNKNOWN),
    (["Kim sings."], "Does Kim dance or Lee sing?", UNKNOWN),
    (["Lee sings."], "Does Kim dance or Lee sing?", YES),
    (["Kim is happy."], "Is Lee happy or Kim happy?", YES),
    (["Kim is happy."], "Is Kim happy or Lee sad?", YES),
    (["Kim is sad."], "Is Kim happy or Lee sad?", UNKNOWN),
])
def test_or_between_two_clauses_in_a_question(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer


def test_the_sentence_is_a_question_with_an_alternative_for_each_side() -> None:
    x = tolk.read("Is Kim happy or Lee happy?")
    assert isinstance(x, lf.Ask) and len(x.alternatives) == 2


def test_the_answer_names_the_side_that_held() -> None:
    m = Mind()
    m.tell("Lee is happy.")
    assert "lee" in m.ask("Is Kim happy or Lee happy?").outcome.lower()


@pytest.mark.parametrize("text", ["Kim is happy or Lee is happy.", "Kim is happy or Lee happy.", "Kim sings or Lee dances.", "Is it true? Kim sings or Lee dances."])
def test_or_in_a_statement_stays_refused(text: str) -> None:
    r = Mind().tell(text)
    assert r.outcome == "refused", text


def test_a_question_that_was_already_read_is_not_read_again() -> None:
    assert Mind().ask("Does Kim sing or does Lee sing?").answer.value == UNKNOWN
    assert Mind().ask("Is Kim happy or sad?").answer.value == UNKNOWN


def test_a_past_tense_question_keeps_the_refusal_it_had() -> None:
    assert Mind().ask("Was Kim happy or Lee sad?").printed == "refuse UNSUPPORTED_TENSE: past on _happy_a_with"


def test_a_sentence_that_still_does_not_read_keeps_its_first_refusal() -> None:
    assert Mind().ask("Is Kim happy or Lee the?").outcome == "refused"

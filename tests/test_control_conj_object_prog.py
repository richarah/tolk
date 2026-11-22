"""Three items, written before the change:
1. A control verb with a conjoined infinitive: "Kim wants to sing and dance." is a claim of each verb (Kim wants to sing; Kim wants to dance).
2. Object control: "Lee wants Kim to sing." is a claim Lee has, about Kim's singing. The world does not hold that Kim sings.
3. Progressive: "Kim is singing." is stored as Kim's singing in progress; "Is Kim singing?" asks for that; "Does Kim sing?" does not match it."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


def run(told: list[str], question: str) -> str:
    m = Mind()
    for s in told:
        m.tell(s)
    return m.ask(question).answer.value


# 1. Conjoined infinitive inside a control claim.
@pytest.mark.parametrize("told, question, answer", [
    (["Kim wants to sing and dance."], "Does Kim want to sing?", YES),
    (["Kim wants to sing and dance."], "Does Kim want to dance?", YES),
    (["Kim wants to sing and dance."], "Does Kim sing?", UNKNOWN),
    (["Kim wants to sing."], "Does Kim want to dance?", UNKNOWN),
])
def test_each_verb_of_a_conjoined_infinitive_is_a_claim(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer


# 2. Object control.
@pytest.mark.parametrize("told, question, answer", [
    (["Lee wants Kim to sing."], "Does Lee want Kim to sing?", YES),
    (["Lee wants Kim to sing."], "Does Kim sing?", UNKNOWN),
    (["Lee wants Kim to sing."], "Does Lee want Kim to dance?", UNKNOWN),
    (["Lee wants Kim to sing."], "Does Kim want to sing?", UNKNOWN),
])
def test_object_control_is_a_claim_of_the_subject(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer


def test_an_object_control_claim_is_stored() -> None:
    m = Mind()
    assert m.tell("Lee wants Kim to sing.").outcome.startswith("stored")
    assert m.db.execute("SELECT COUNT(*) FROM claim").fetchone()[0] == 1


# 3. Progressive.
@pytest.mark.parametrize("told, question, answer", [
    (["Kim is singing."], "Is Kim singing?", YES),
    (["Kim is singing."], "Does Kim sing?", UNKNOWN),
    (["Kim sings."], "Is Kim singing?", UNKNOWN),
    (["Kim was singing."], "Was Kim singing?", YES),
    (["Kim is singing."], "Is Lee singing?", UNKNOWN),
    (["Kim is singing."], "Is Kim dancing?", UNKNOWN),
])
def test_a_progressive_is_asked_as_a_progressive(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer


def test_a_progressive_statement_is_stored() -> None:
    m = Mind()
    assert m.tell("Kim is singing.").outcome.startswith("stored")
    assert m.db.execute("SELECT COUNT(*) FROM fact WHERE pred = 'modal' AND a1 = 'prog'").fetchone()[0] == 1


@pytest.mark.parametrize("text", ["Kim had sung.", "Kim will have sung.", "Kim will be singing."])
def test_perfect_and_future_progressive_stay_refused(text: str) -> None:
    assert Mind().tell(text).outcome == "refused"


def test_a_supposed_progressive_is_dropped() -> None:
    m = Mind()
    m.suppose("Kim is singing.")
    assert m.ask("Is Kim singing?").answer.value == YES
    m.drop()
    assert m.ask("Is Kim singing?").answer.value == UNKNOWN

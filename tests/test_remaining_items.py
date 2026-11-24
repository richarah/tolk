"""The remaining items:
1. A negated progressive: stored since the negated-events item, on the negated fact's own event (see the test below).
2. A question about a conjunction inside a control claim: "Does Kim want to sing and dance?" is Yes when both claims are told; "Does Kim
   want to sing or dance?" is Yes when either is."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


def run(told: list[str], question: str) -> str:
    m = Mind()
    for s in told:
        m.tell(s)
    return m.ask(question).answer.value


def test_a_negated_progressive_is_stored_on_the_negated_event() -> None:
    # Was refused: a negated fact had no event to carry the progressive. Since the negated-events item it has one.
    m = Mind()
    assert m.tell("Kim is not singing.").outcome.startswith("stored")
    assert m.ask("Is Kim singing?").answer.value == NO
    assert m.ask("Does Kim sing?").answer.value == UNKNOWN


@pytest.mark.parametrize("told, question, answer", [
    (["Kim wants to sing and dance."], "Does Kim want to sing and dance?", YES),
    (["Kim wants to sing."], "Does Kim want to sing and dance?", UNKNOWN),
    (["Kim wants to sing."], "Does Kim want to sing or dance?", YES),
    (["Kim wants to dance."], "Does Kim want to sing or dance?", YES),
    (["Kim wants to swim."], "Does Kim want to sing or dance?", UNKNOWN),
])
def test_a_question_about_a_conjunction_of_claims(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer

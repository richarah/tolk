"""The remaining items:
1. A negated progressive: stays refused; negated facts have no event to carry the progressive (see the test below).
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


def test_a_negated_progressive_stays_refused_because_negated_facts_have_no_event() -> None:
    # Known limit (DECISIONS.md, remaining items): a negated fact is stored without an event, so the progressive has nothing to attach to.
    assert Mind().tell("Kim is not singing.").outcome == "refused"


@pytest.mark.parametrize("told, question, answer", [
    (["Kim wants to sing and dance."], "Does Kim want to sing and dance?", YES),
    (["Kim wants to sing."], "Does Kim want to sing and dance?", UNKNOWN),
    (["Kim wants to sing."], "Does Kim want to sing or dance?", YES),
    (["Kim wants to dance."], "Does Kim want to sing or dance?", YES),
    (["Kim wants to swim."], "Does Kim want to sing or dance?", UNKNOWN),
])
def test_a_question_about_a_conjunction_of_claims(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer

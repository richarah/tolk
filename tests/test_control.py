"""Control verbs: "Kim wants to sing." is a claim Kim has, that Kim sings. The world does not hold that Kim sings. Subject control only:
the infinitive's subject is the verb's subject. Object control ("Lee wants Kim to sing.") and a negated control verb stay refused.
Written before the change."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


def run(told: list[str], question: str) -> str:
    m = Mind()
    for s in told:
        m.tell(s)
    return m.ask(question).answer.value


@pytest.mark.parametrize("told, question, answer", [
    (["Kim wants to sing."], "Does Kim want to sing?", YES),
    (["Kim wants to sing."], "Does Kim sing?", UNKNOWN),
    (["Kim wants to sing."], "Does Lee want to sing?", UNKNOWN),
    (["Kim tries to sing."], "Does Kim try to sing?", YES),
    (["Kim wants to sing."], "Does Kim want to dance?", UNKNOWN),
    (["Kim wants to sing.", "Kim sings."], "Does Kim sing?", YES),
])
def test_a_control_verb_is_a_claim_of_the_subject(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer


def test_a_control_statement_is_stored_as_a_claim() -> None:
    m = Mind()
    assert m.tell("Kim wants to sing.").outcome.startswith("stored")
    assert m.db.execute("SELECT COUNT(*) FROM claim").fetchone()[0] == 1


@pytest.mark.parametrize("text", ["Lee wants Kim to sing."])
def test_object_control_stays_refused(text: str) -> None:
    assert Mind().tell(text).outcome == "refused"


def test_a_negated_control_verb_is_a_negated_claim_as_a_negated_belief_is() -> None:
    m = Mind()
    m.tell("Kim does not want to sing.")
    assert m.ask("Does Kim not want to sing?").answer.value == YES
    assert m.ask("Does Kim want to sing?").answer.value == NO


def test_a_claim_inside_a_supposition_is_still_refused_as_before() -> None:
    # Claims in a supposition are not stored (tests/test_phase21.py); a control claim is a claim.
    assert Mind().suppose("Kim wants to sing.").outcome.startswith("refused")

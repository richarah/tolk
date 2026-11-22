"""Modals: can, must, might, should, may, could, would are stored on the event they modify, as modal(event, kind), and asked as a
question about that event. A plain question does not match an event that has a modal; a modal question does not match a plain fact.
Negated modals and modals in rules stay refused. Written before the change."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


def run(told: list[str], question: str) -> str:
    m = Mind()
    for s in told:
        m.tell(s)
    return m.ask(question).answer.value


@pytest.mark.parametrize("told, question, answer", [
    (["Kim can sing."], "Can Kim sing?", YES),
    (["Kim can sing."], "Does Kim sing?", UNKNOWN),
    (["Kim sings."], "Can Kim sing?", UNKNOWN),
    (["Kim must sing."], "Must Kim sing?", YES),
    (["Kim must sing."], "Can Kim sing?", UNKNOWN),
    (["Kim might sing."], "Might Kim sing?", YES),
    (["Kim should sing."], "Should Kim sing?", YES),
    (["Kim may sing."], "May Kim sing?", YES),
    (["Kim could sing."], "Could Kim sing?", YES),
    (["Kim would sing."], "Would Kim sing?", YES),
    (["Kim sings.", "Kim can dance."], "Does Kim sing?", YES),
    (["Kim sings.", "Kim can dance."], "Can Kim dance?", YES),
    (["Kim sings.", "Kim can dance."], "Can Kim sing?", UNKNOWN),
    (["Kim can sing."], "Can Lee sing?", UNKNOWN),
])
def test_a_modal_is_stored_and_asked_as_a_modal(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer


def test_a_modal_statement_is_stored() -> None:
    m = Mind()
    assert m.tell("Kim can sing.").outcome.startswith("stored")
    assert m.db.execute("SELECT COUNT(*) FROM fact WHERE pred = 'modal' AND a1 = 'can'").fetchone()[0] == 1


@pytest.mark.parametrize("text", ["Kim cannot sing.", "Kim must not sing.", "Every bird can fly.", "Kim can sing and dance or Lee sings."])
def test_negated_and_rule_modals_stay_refused(text: str) -> None:
    assert Mind().tell(text).outcome == "refused"


def test_a_supposed_modal_is_dropped() -> None:
    m = Mind()
    m.suppose("Kim can sing.")
    assert m.ask("Can Kim sing?").answer.value == YES
    m.drop()
    assert m.ask("Can Kim sing?").answer.value == UNKNOWN


def test_a_repeated_modal_is_already_told() -> None:
    m = Mind()
    m.tell("Kim can sing.")
    assert m.tell("Kim can sing.").outcome.startswith("already told")

"""Medium item M3: future and present perfect are stored and asked. Past perfect and future perfect, and the progressive, stay refused.
A present perfect is stored as a past event, because the store has no "now": "Kim has sung." is a sung event Kim has in the past."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


def run(told: list[str], question: str) -> str:
    m = Mind()
    for s in told:
        m.tell(s)
    return m.ask(question).answer.value


def test_a_future_event_is_stored() -> None:
    m = Mind()
    assert m.tell("Kim will sing.").outcome.startswith("stored")
    assert m.db.execute("SELECT COUNT(*) FROM fact WHERE pred = 'tense' AND a1 = 'fut'").fetchone()[0] == 1


@pytest.mark.parametrize("told, question, answer", [
    (["Kim will sing."], "Will Kim sing?", YES),
    (["Kim will sing."], "Does Kim sing?", UNKNOWN),
    (["Kim will sing."], "Did Kim sing?", UNKNOWN),
    (["Kim will sing."], "Will Lee sing?", UNKNOWN),
    (["Kim sang.", "Kim will sing."], "Did Kim sing?", YES),
    (["Kim sang.", "Kim will sing."], "Will Kim sing?", YES),
    (["Kim sang."], "Will Kim sing?", UNKNOWN),
])
def test_a_future_is_asked_with_will(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer


def test_a_present_perfect_is_stored_as_a_past_event() -> None:
    m = Mind()
    assert m.tell("Kim has sung.").outcome.startswith("stored")
    assert m.db.execute("SELECT COUNT(*) FROM fact WHERE pred = 'tense' AND a1 = 'past'").fetchone()[0] == 1


@pytest.mark.parametrize("told, question, answer", [
    (["Kim has sung."], "Has Kim sung?", YES),
    (["Kim has sung."], "Did Kim sing?", YES),
    (["Kim has sung."], "Does Kim sing?", UNKNOWN),
    (["Kim has sung."], "Will Kim sing?", UNKNOWN),
])
def test_a_present_perfect_is_asked_as_a_past(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer


@pytest.mark.parametrize("text, code", [
    ("Kim had sung.", "UNSUPPORTED_ASPECT"),
    ("Kim will have sung.", "UNSUPPORTED_ASPECT"),
    ("Kim is singing.", "UNSUPPORTED_ASPECT"),
])
def test_past_perfect_future_perfect_and_progressive_stay_refused(text: str, code: str) -> None:
    r = Mind().tell(text)
    assert r.outcome == "refused" and r.printed.startswith(f"refuse {code}"), r.printed


def test_a_future_inside_a_supposition_is_stored_and_dropped() -> None:
    m = Mind()
    m.suppose("Kim will sing.")
    assert m.ask("Will Kim sing?").answer.value == YES
    m.drop()
    assert m.ask("Will Kim sing?").answer.value == UNKNOWN


def test_a_repeated_future_is_already_told() -> None:
    m = Mind()
    m.tell("Kim will sing.")
    assert m.tell("Kim will sing.").outcome.startswith("already told")

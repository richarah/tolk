"""Tier C: the dialogue table in SPEC.md, run in order through Mind."""

import pytest

from tolk import say
from tolk.ask import UNKNOWN, YES
from tolk.mind import Mind


@pytest.fixture(scope="module")
def mind() -> Mind:
    m = Mind()
    assert m.tell("Kim lives in Oslo.").outcome.startswith("stored")
    return m


def test_who_lives_in_oslo_is_kim(mind: Mind) -> None:
    r = mind.ask("Who lives in Oslo?")
    assert say.answer_text(mind.db, r.answer) == "Kim"


def test_where_does_kim_live_is_oslo(mind: Mind) -> None:
    r = mind.ask("Where does Kim live?")
    assert say.answer_text(mind.db, r.answer) == "Oslo"


def test_does_kim_live_in_oslo_is_yes(mind: Mind) -> None:
    r = mind.ask("Does Kim live in Oslo?")
    assert r.answer.value == YES
    assert r.printed == "ask    _live_v_1(E, kim), _in_p_loc(E, oslo)"


def test_does_kim_live_in_bergen_is_unknown(mind: Mind) -> None:
    r = mind.ask("Does Kim live in Bergen?")
    assert r.answer.value == UNKNOWN
    assert r.printed == "ask    _live_v_1(E, kim), _in_p_loc(E, bergen)"


def test_sandy_arrived_gets_a_past_tense_fact(mind: Mind) -> None:
    r = mind.tell("Sandy arrived.")
    assert r.outcome.startswith("stored")
    past = mind.db.execute(
        "SELECT COUNT(*) FROM fact f JOIN fact t ON t.pred = 'tense' AND t.a0 = f.a0 "
        "WHERE f.pred = '_arrive_v_1' AND t.a1 = 'past'"
    ).fetchone()[0]
    assert past == 1

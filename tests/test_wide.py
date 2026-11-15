"""Item 1: when the first five readings give a refusal, the sentence is parsed again with 25 and chosen again by the same order."""

from tolk import choice, compile as comp, lf
from tolk.mind import Mind
from helpers import wide_readings_of


def test_a_sentence_whose_right_reading_is_the_sixth_becomes_a_rule() -> None:
    r = Mind().tell("If Rio hums, Pip hums.")
    assert r.printed == "rule   _hum_v_1(E!, pip) :- _hum_v_1(E1, rio)"
    assert r.outcome == "rule stored"
    assert r.of == 25


def test_the_wide_fixture_has_the_sixth_reading_as_the_one_that_compiles() -> None:
    readings = wide_readings_of("If Rio hums, Pip hums.")
    assert len(readings) == 25
    k, x = comp.choose(readings, set(), after=5)
    assert k == 5 and not isinstance(x, lf.Refusal)
    assert k in choice.preferred(readings, set())


def test_a_refused_sentence_with_fewer_than_five_readings_is_not_parsed_again() -> None:
    from tolk import erg
    calls = []
    real = erg.parse
    erg.parse = lambda text, tags=None, limit=erg.READINGS: (calls.append(limit), real(text, tags, limit))[1]
    try:
        r = Mind().tell("Every blorp flibbers.")
    finally:
        erg.parse = real
    assert r.outcome == "refused" and calls == [erg.READINGS]

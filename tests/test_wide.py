"""Item 1: when the first five readings give a refusal, the sentence is parsed again with 25 and chosen again by the same order."""

import pytest

from tolk import lf

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
        r = Mind().tell("Kim tries to sing.")
    finally:
        erg.parse = real
    assert r.outcome == "refused" and calls == [erg.READINGS]


UNDERSTOOD_AND_DECLINED = [
    ("Kim owns more than two cats.", "UNSUPPORTED_PREDICATE"),
    ("Kim and Lee like Rio or Pip.", "COORDINATION"),
    ("Kim saw Lee in the park with Rio.", "DEFINITE_MATCHES"),
    ("Kim told Lee that Rio sings or hums.", "TOO_MANY_ARGUMENTS"),  # was UNSUPPORTED_TENSE before the or-clause tense rule
    ("If Kim sings or Lee dances, Rio hums.", "COORDINATION"),
    ("Kim sings, Lee dances, or Rio hums.", "COORDINATION"),
    ("Kim gave Lee a book and Pip a pen.", "UNSUPPORTED_PREDICATE"),
    ("Most dogs bark.", "UNSUPPORTED_QUANTIFIER"),
    ("Kim can sing and Lee can dance or hum.", "COORDINATION"),
    ("Few dogs bark loudly at night.", "UNSUPPORTED_QUANTIFIER"),
]


@pytest.mark.parametrize("text, code", UNDERSTOOD_AND_DECLINED)
def test_a_reading_that_was_understood_and_declined_keeps_its_refusal_with_the_wider_search_on(text: str, code: str) -> None:
    from tolk import erg
    limits = []
    real = erg.parse
    erg.parse = lambda t, tags=None, limit=erg.READINGS: (limits.append(limit), real(t, tags, limit))[1]
    try:
        r = Mind().tell(text)
    finally:
        erg.parse = real
    assert r.outcome == "refused" and r.printed.startswith(f"refuse {code}"), r.printed
    if lf.is_final(lf.Refusal(code, "")):
        assert erg.WIDE not in limits, "a final refusal ends the search: no wider parse"

"""Item 2: a sentence the grammar cannot read, with a word taken for a name, must be a refusal, never an exception. The cause was `reading.read`
returning the readings it had set aside together with the choice made among others; a choice then pointed past the end of the list."""

import pytest

from tolk import lf, reading
from tolk.mind import Mind

BAD = ["A blips sleeps.", "Tweety is a blips.", "Blips a sleeps.", "The blips sleeps.", "Some quorls sleeps."]


@pytest.mark.parametrize("text", BAD)
def test_an_ungrammatical_sentence_is_a_refusal_not_an_error(text: str) -> None:
    r = Mind().tell(text)
    assert r.outcome == "refused"


def test_a_blips_sleeps_is_refused_for_the_word() -> None:
    r = Mind().tell("A blips sleeps.")
    assert r.printed == "refuse UNKNOWN_WORD blips" or "UNKNOWN_WORD" in r.printed


@pytest.mark.parametrize("text", BAD + ["Kim sleeps.", "Every cat sleeps.", "", ".", "A", "sleeps", "Is?"])
def test_the_chosen_index_is_always_inside_the_readings_or_the_result_is_a_refusal(text: str) -> None:
    readings, k, x = reading.read(set(), {}, text)
    assert isinstance(x, lf.Refusal) or 0 <= k < len(readings)

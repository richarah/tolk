"""The parser's tagged input (-y), from recorded fixtures: what it gives for the unknown-word sentences of phase 16.
The parser's own manual does not describe the option; the binary's message says "provide input pre-tokenized in YY format (-y)"."""

import json

import pytest

from helpers import FIXTURES, fixture_path
from tolk import compile as comp, lf, sem

EXPECTED = {
    "Tweety is a blorp.": "tell   _blorp_n_unknown(tweety)",
    "Tweety flibbers.": "tell   _flibber_v_unknown(e1, tweety)",
    "Does Tweety flibber?": "ask    _flibber_v_unknown(E, tweety)",
    "Is Tweety a blorp?": "ask    _blorp_n_unknown(tweety)",
    "Every blorp flibbers.": "rule   _flibber_v_unknown(E!, X) :- _blorp_n_unknown(X)",
    "Tweety is glorpy.": "tell   _glorpy_a_unknown(e1, tweety)",
    "Is Tweety glorpy?": "ask    _glorpy_a_unknown(E, tweety)",
}


@pytest.mark.parametrize("text", EXPECTED)
def test_the_tagged_fixture_compiles_to_the_stored_shape(text: str) -> None:
    record = json.loads((FIXTURES / "tagged" / fixture_path(text).name).read_text())
    readings = [sem.read(r["simplemrs"], r["lexical"]) for r in record["readings"]]
    assert lf.show(comp.choose(readings, set())[1]) == EXPECTED[text]


def test_the_untagged_parse_of_two_unknown_words_has_no_reading_and_the_tagged_one_has() -> None:
    assert json.loads(fixture_path("Every blorp flibbers.").read_text())["readings"] == []
    assert json.loads((FIXTURES / "tagged" / fixture_path("Every blorp flibbers.").name).read_text())["readings"]

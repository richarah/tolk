import json

import pytest

from helpers import fixture_path, sentences
from tolk import sem


def load(text: str) -> dict:
    return json.loads(fixture_path(text).read_text())


# SPEC phase 0: a sentence with no reading is an expected failure with its reason; the only permitted use of xfail.
NO_READING = {"Every blorp flibbers.": "the grammar gives no reading when two words in a sentence are unknown to it (PROGRESS.md, Open)"}
CASES = [pytest.param(t, marks=pytest.mark.xfail(strict=True, reason=NO_READING[t])) if t in NO_READING else t for t in sentences()]


@pytest.mark.parametrize("text", CASES)
def test_every_sentence_has_a_reading(text: str) -> None:
    fixture = load(text)
    assert fixture["text"] == text
    assert len(fixture["readings"]) >= 1


@pytest.mark.parametrize("text", sentences())
def test_stored_neutral_matches_raw(text: str) -> None:
    for reading in load(text)["readings"]:
        assert sem.to_dict(sem.read(reading["simplemrs"])) == reading["neutral"]

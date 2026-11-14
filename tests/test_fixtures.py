import json

import pytest

from helpers import fixture_path, sentences
from tolk import sem


def load(text: str) -> dict:
    return json.loads(fixture_path(text).read_text())


@pytest.mark.parametrize("text", sentences())
def test_every_sentence_has_a_reading(text: str) -> None:
    fixture = load(text)
    assert fixture["text"] == text
    assert len(fixture["readings"]) >= 1


@pytest.mark.parametrize("text", sentences())
def test_stored_neutral_matches_raw(text: str) -> None:
    for reading in load(text)["readings"]:
        assert sem.to_dict(sem.read(reading["simplemrs"])) == reading["neutral"]

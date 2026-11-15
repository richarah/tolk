import json

import pytest

from helpers import fixture_path, sentences
from tolk import sem


def load(text: str) -> dict:
    return json.loads(fixture_path(text).read_text())


def readings_of_fixture(text: str) -> list:
    """The readings the parser gave; for a sentence with none, those it gives with the unknown words tagged (finish, item 3)."""
    found = load(text)["readings"]
    tagged = fixture_path(text).parent / "tagged" / fixture_path(text).name
    return found or (json.loads(tagged.read_text())["readings"] if tagged.exists() else [])


CASES = sentences()


@pytest.mark.parametrize("text", CASES)
def test_every_sentence_has_a_reading(text: str) -> None:
    fixture = load(text)
    assert fixture["text"] == text
    assert len(readings_of_fixture(text)) >= 1


@pytest.mark.parametrize("text", sentences())
def test_stored_neutral_matches_raw(text: str) -> None:
    for reading in load(text)["readings"]:
        assert sem.to_dict(sem.read(reading["simplemrs"])) == reading["neutral"]

"""Phase 12: negation over bare and indefinite nouns, and negated questions. The dialogue is SPEC2's; the rest are other words."""

import pytest

from tolk.ask import CONFLICT, NO, UNKNOWN, YES
from tolk.mind import Mind


def run(told: list[str], question: str) -> str:
    m = Mind()
    for s in told:
        m.tell(s)
    return m.ask(question).answer.value


FISH = ["Kim does not like fish.", "Nemo is a fish."]


def test_the_rule_is_printed_as_specified() -> None:
    assert Mind().tell("Kim does not like fish.").printed == "rule   not _like_v_1(_, kim, X) :- _fish_n_1(X)"


@pytest.mark.parametrize("question, answer", [
    ("Does Kim like Nemo?", NO), ("Does Kim like Tweety?", UNKNOWN),
    ("Does Kim not like Nemo?", YES), ("Does Kim not like Tweety?", UNKNOWN),
])
def test_the_dialogue(question: str, answer: str) -> None:
    assert run(FISH, question) == answer


def test_the_no_answer_has_a_proof() -> None:
    m = Mind()
    for s in FISH:
        m.tell(s)
    out = m.ask("Does Kim like Nemo?").outcome
    # The derived negative fact keeps its template wording: its generated sentence has an event the fact does not, so it is not accepted.
    assert "not like(kim, nemo)  (by rule 1)" in out and "Nemo is a fish.  (told:" in out


@pytest.mark.parametrize("told, question, answer", [
    (["Ada does not like cats.", "Tom is a cat."], "Does Ada like Tom?", NO),
    (["Ada does not like cats.", "Tom is a cat."], "Does Ada not like Tom?", YES),
    (["Ada does not like cats.", "Tom is a cat."], "Does Ada not like Bo?", UNKNOWN),
    (["Pingu does not fly."], "Does Pingu not fly?", YES),
    (["Pingu does not fly."], "Does Pingu fly?", NO),
    (["Kim is not a robin."], "Is Kim not a robin?", YES),
    (["Kim is not a robin."], "Is Kim a robin?", NO),
    (["Kim is a robin."], "Is Kim not a robin?", NO),
    (["Bo owns no dog.", "Rex is a dog."], "Does Bo not own Rex?", YES),
    ([], "Does Pingu not fly?", UNKNOWN),
])
def test_other_words(told: list[str], question: str, answer: str) -> None:
    assert run(told, question) == answer


def test_a_negated_question_in_a_conflict_is_a_conflict() -> None:
    told = ["Pingu is a penguin.", "Pingu does not fly.", "Every penguin is a bird.", "Every bird flies."]
    assert run(told, "Does Pingu not fly?") == CONFLICT

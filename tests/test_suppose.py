"""Suppositions: a statement in a new context that inherits the world. Dropping it removes it and nothing else."""

import pytest

from tolk.ask import CONFLICT, YES
from tolk.mind import Mind

TIER_A = [
    "Tweety is a robin.", "Every robin is a bird.", "Every bird flies.", "Birds are animals.",
    "Tweety sings.", "Every robin that sings is happy.", "Kim is a person.", "Kim owns a dog.",
    "Every person who owns a dog is happy.", "Kim likes Sandy.", "Rex is a dog.", "Every dog has an owner.",
]


@pytest.fixture()
def mind() -> Mind:
    m = Mind()
    for s in TIER_A + ["Pingu is a penguin.", "Pingu does not fly.", "No penguin flies."]:
        m.tell(s)
    return m


def facts(m: Mind) -> int:
    return m.db.execute("SELECT COUNT(*) FROM fact").fetchone()[0]


def test_supposed_penguin_makes_tweety_conflict_inside_only(mind: Mind) -> None:
    assert mind.ask("Does Tweety fly?").answer.value == YES
    before = facts(mind)
    assert mind.suppose("Tweety is a penguin.").outcome.startswith("stored")
    assert mind.ask("Does Tweety fly?").answer.value == CONFLICT
    mind.drop()
    assert mind.ask("Does Tweety fly?").answer.value == YES
    assert facts(mind) == before


def test_dropping_removes_the_supposition_and_its_conflicts(mind: Mind) -> None:
    mind.suppose("Tweety is a penguin.")
    assert mind.db.execute("SELECT COUNT(*) FROM fact WHERE ctx != 'world'").fetchone()[0] > 0
    mind.drop()
    assert mind.db.execute("SELECT COUNT(*) FROM fact WHERE ctx != 'world'").fetchone()[0] == 0
    assert mind.db.execute("SELECT COUNT(*) FROM conflict").fetchone()[0] == 0


def test_drop_without_a_supposition_is_an_error(mind: Mind) -> None:
    with pytest.raises(ValueError):
        mind.drop()

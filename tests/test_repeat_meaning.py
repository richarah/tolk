"""A statement that means what a told statement means adds nothing: the same atoms about the same things, in any order and with fresh
things renamed. Wording is not compared. Written first; the passive failed (it stored a second dog)."""

from tolk.mind import Mind


def facts(m: Mind) -> int:
    return m.db.execute("SELECT COUNT(*) FROM fact").fetchone()[0]


def test_a_passive_of_a_told_sentence_adds_nothing() -> None:
    m = Mind()
    m.tell("Kim owns a dog.")
    n = facts(m)
    r = m.tell("A dog is owned by Kim.")
    assert r.outcome.startswith("already told"), r.outcome
    assert facts(m) == n


def test_a_negated_passive_adds_nothing() -> None:
    m = Mind()
    m.tell("Kim does not own a dog.")
    n = m.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0]
    assert m.tell("A dog is not owned by Kim.").outcome.startswith("already told")
    assert m.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0] == n


def test_a_different_thing_is_still_stored() -> None:
    m = Mind()
    m.tell("Kim owns a dog.")
    assert m.tell("Lee owns a dog.").outcome.startswith("stored")
    assert m.tell("Kim owns a cat.").outcome.startswith("stored")


def test_a_different_relation_is_still_stored() -> None:
    m = Mind()
    m.tell("Kim owns a dog.")
    assert m.tell("Kim likes a dog.").outcome.startswith("stored")


def test_the_repeat_quotes_the_sentence_it_repeats() -> None:
    m = Mind()
    m.tell("Kim owns a dog.")
    assert m.tell("A dog is owned by Kim.").outcome == 'already told: "Kim owns a dog."'


def test_a_repeat_that_was_forgotten_is_stored_again() -> None:
    m = Mind()
    m.tell("Kim owns a dog.")
    m.tell("Forget that Kim owns a dog.")
    assert m.tell("A dog is owned by Kim.").outcome.startswith("stored")

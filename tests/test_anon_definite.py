"""Small item S1: a definite that refers to an anonymous thing ("the dog") leaves that thing an anonymous thing, with no name row.
The constant a definite gives is tagged named, but the store must keep the thing's own kind."""

from tolk.mind import Mind


def test_a_definite_referring_to_an_anonymous_thing_keeps_its_kind() -> None:
    m = Mind()
    m.tell("Kim owns a dog.")
    assert m.tell("The dog barks.").outcome.startswith("stored")
    assert m.db.execute("SELECT kind FROM entity WHERE id = 'a1'").fetchone() == ("anon",)


def test_no_name_row_is_made_for_an_anonymous_thing() -> None:
    m = Mind()
    m.tell("Kim owns a dog.")
    m.tell("The dog barks.")
    assert m.db.execute("SELECT COUNT(*) FROM name WHERE entity = 'a1'").fetchone()[0] == 0
    assert m.db.execute("SELECT COUNT(*) FROM name WHERE text = 'a1'").fetchone()[0] == 0

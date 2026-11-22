"""A fact told in a supposition defeats a default of the world inside that supposition, and the defeat is gone when the supposition is dropped.
Written as the failing test for the limit recorded in DECISIONS.md (medium-items pass); the old test asserted the Conflict."""

from tolk.ask import NO, YES
from tolk.mind import Mind


def test_a_supposed_fact_defeats_a_world_default_inside_the_supposition() -> None:
    m = Mind()
    m.tell("Birds fly.")
    m.tell("Tweety is a bird.")
    m.suppose("Tweety does not fly.")
    assert m.ask("Does Tweety fly?").answer.value == NO


def test_the_defeat_is_gone_after_drop() -> None:
    m = Mind()
    m.tell("Birds fly.")
    m.tell("Tweety is a bird.")
    m.suppose("Tweety does not fly.")
    m.drop()
    assert m.ask("Does Tweety fly?").answer.value == YES
    assert m.db.execute("SELECT COUNT(*) FROM defeat WHERE ctx != 'world'").fetchone()[0] == 0


def test_the_world_default_still_answers_in_the_world() -> None:
    m = Mind()
    m.tell("Birds fly.")
    m.tell("Tweety is a bird.")
    m.suppose("Tweety does not fly.")
    m.drop()
    assert m.ask("Does Tweety fly?").answer.value == YES
    assert m.ask("Does Tweety fly?").outcome.startswith("Yes")


def test_a_supposed_fact_defeat_does_not_change_the_world_rebuild() -> None:
    m = Mind()
    m.tell("Birds fly.")
    m.tell("Tweety is a bird.")
    before = sorted(m.db.execute("SELECT pred, a0, positive, level FROM fact WHERE ctx = 'world'").fetchall())
    m.suppose("Tweety does not fly.")
    m.drop()
    assert sorted(m.db.execute("SELECT pred, a0, positive, level FROM fact WHERE ctx = 'world'").fetchall()) == before


def test_a_supposed_fact_that_does_not_clash_leaves_the_default_in_force() -> None:
    m = Mind()
    m.tell("Birds fly.")
    m.tell("Tweety is a bird.")
    m.suppose("Tweety sleeps.")
    assert m.ask("Does Tweety fly?").answer.value == YES

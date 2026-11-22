"""Medium item M1 and M2: rules and identity merges inside a supposition, held in a context column, and removed by drop().
Written before the change; each test failed on the release before it was made to pass."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


def test_a_rule_inside_a_supposition_is_stored_and_answers_inside_it() -> None:
    m = Mind()
    m.suppose("Every bird is an animal.")
    m.tell("Tweety is a bird.")
    assert m.ask("Is Tweety an animal?").answer.value == YES


def test_a_supposed_rule_is_not_in_force_after_drop() -> None:
    m = Mind()
    m.suppose("Every bird is an animal.")
    m.tell("Tweety is a bird.")
    m.drop()
    assert m.ask("Is Tweety an animal?").answer.value == UNKNOWN


def test_a_world_rule_applies_inside_a_supposition() -> None:
    m = Mind()
    m.tell("Every bird is an animal.")
    m.suppose("Tweety is a bird.")
    assert m.ask("Is Tweety an animal?").answer.value == YES
    m.drop()
    assert m.ask("Is Tweety an animal?").answer.value == UNKNOWN


def test_a_supposed_rule_does_not_leak_into_the_world_rules() -> None:
    m = Mind()
    m.tell("Every bird flies.")
    m.suppose("Every bird is an animal.")
    m.drop()
    assert m.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0] == 1
    assert m.db.execute("SELECT COUNT(*) FROM rule WHERE ctx = 'world'").fetchone()[0] == 1


def test_drop_removes_the_supposed_rule_row() -> None:
    m = Mind()
    m.suppose("Every bird is an animal.")
    m.drop()
    assert m.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0] == 0


def test_a_supposed_identity_answers_inside_it_only() -> None:
    m = Mind()
    m.tell("Kim is happy.")
    m.suppose("Pip is Kim.")
    assert m.ask("Is Pip happy?").answer.value == YES
    m.drop()
    assert m.ask("Is Pip happy?").answer.value == UNKNOWN


def test_drop_restores_the_identity_tables() -> None:
    m = Mind()
    m.tell("Kim is happy.")
    before = {t: sorted(m.db.execute(f"SELECT * FROM {t}").fetchall()) for t in ("merge", "entity", "name")}
    m.suppose("Pip is Kim.")
    m.drop()
    assert {t: sorted(m.db.execute(f"SELECT * FROM {t}").fetchall()) for t in ("merge", "entity", "name")} == before


def test_a_supposed_identity_does_not_rewrite_the_world() -> None:
    m = Mind()
    m.tell("Pip is a dog.")
    m.suppose("Pip is Kim.")
    assert m.db.execute("SELECT COUNT(*) FROM fact WHERE a0 = 'pip' AND ctx = 'world'").fetchone()[0] >= 1
    assert m.db.execute("SELECT COUNT(*) FROM merge WHERE ctx = 'world'").fetchone()[0] == 0


def test_the_dump_is_the_same_after_a_supposed_rule_and_identity() -> None:
    m = Mind()
    for s in ["Tweety is a robin.", "Every robin is a bird.", "Kim is happy."]:
        m.tell(s)
    before = {t: sorted(m.db.execute(f"SELECT * FROM {t}").fetchall()) for t in ("sentence", "entity", "name", "fact", "why", "rule", "merge", "conflict")}
    m.suppose("Every bird is an animal.")
    m.tell("Tweety is a robin.")
    m.drop()
    assert {t: sorted(m.db.execute(f"SELECT * FROM {t}").fetchall()) for t in before} == before


def test_a_universal_question_inside_a_supposition_sees_the_supposed_rule() -> None:
    m = Mind()
    m.suppose("Every bird flies.")
    assert m.ask("Does every bird fly?").answer.value == YES
    m.drop()
    assert m.ask("Does every bird fly?").answer.value == UNKNOWN


def test_a_supposed_fact_against_a_world_default_is_answered_no_inside_and_yes_after_drop() -> None:
    # Was the known limit "reported as a conflict"; a fact told in the supposition now defeats the world default there (tests/test_defeat_ctx.py).
    m = Mind()
    m.tell("Birds fly.")
    m.tell("Tweety is a bird.")
    m.suppose("Tweety does not fly.")
    assert m.ask("Does Tweety fly?").answer.value == NO
    m.drop()
    assert m.ask("Does Tweety fly?").answer.value == YES

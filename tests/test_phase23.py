"""Phase 23: morphology of unknown words. The dialogue is SPEC2's; the rest use other words. Expectations were written before the code."""

import pytest

from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


def rules(m: Mind) -> int:
    return m.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0]


@pytest.fixture()
def mind() -> Mind:
    m = Mind()
    for s in ("Tweety is a blorp.", "Tweety is glorpy.", "Tweety flibbers."):
        m.tell(s)
    return m


def test_un_makes_the_word_hold_exactly_when_the_base_does_not(mind: Mind) -> None:
    r = mind.tell("Rex is unglorpy.")
    assert r.printed.splitlines()[-1] == "note   unglorpy = un + glorpy"
    assert mind.ask("Is Rex glorpy?").answer.value == NO


def test_er_is_a_thing_that_does_the_verb(mind: Mind) -> None:
    r = mind.tell("Pingu is a flibberer.")
    assert r.printed.splitlines()[-1] == "note   flibberer = er + flibber"
    assert mind.ask("Does Pingu flibber?").answer.value == YES


def test_able_is_recorded_and_adds_no_rule(mind: Mind) -> None:
    before = rules(mind)
    r = mind.tell("Tweety is flibberable.")
    assert r.outcome.startswith("stored") and r.printed.splitlines()[-1] == "note   flibberable = able + flibber"
    assert rules(mind) == before
    assert mind.db.execute("SELECT word, base, affix FROM morph").fetchall() == [("_flibberable_a_unknown", "_flibber_v_unknown", "able")]


def test_describe_mentions_the_split(mind: Mind) -> None:
    mind.tell("Rex is unglorpy.")
    assert "unglorpy = un + glorpy" in mind.ask("Who is Rex?").outcome


def test_the_split_is_recorded_and_two_strict_rules_are_stored(mind: Mind) -> None:
    before = rules(mind)
    mind.tell("Rex is unglorpy.")
    assert mind.db.execute("SELECT word, base, affix FROM morph").fetchall() == [("_unglorpy_a_unknown", "_glorpy_a_unknown", "un")]
    assert rules(mind) == before + 2


def test_a_base_that_is_not_in_the_store_leaves_the_word_whole() -> None:
    m = Mind()
    r = m.tell("Bo is zorpable.")
    assert r.outcome.startswith("stored") and "note" not in r.printed
    assert m.db.execute("SELECT COUNT(*) FROM morph").fetchone()[0] == 0 and rules(m) == 0


def test_a_base_of_the_wrong_class_leaves_the_word_whole() -> None:
    m = Mind()
    m.tell("Ada is a zorp.")
    assert "note" not in m.tell("Ada is zorpable.").printed


def test_non_is_a_prefix_like_un() -> None:
    m = Mind()
    m.tell("Ada is zorpy.")
    m.tell("Pip is nonzorpy.")
    assert m.ask("Is Pip zorpy?").answer.value == NO
    assert m.ask("Is Ada zorpy?").answer.value == YES


def test_the_base_of_a_derived_adjective_that_holds_makes_the_other_not_hold() -> None:
    m = Mind()
    m.tell("Ada is zorpy.")
    m.tell("Pip is nonzorpy.")
    m.tell("Cy is zorpy.")
    assert m.ask("Is Cy nonzorpy?").answer.value == NO


def test_a_conflict_is_reported_when_the_new_word_contradicts_what_was_told() -> None:
    m = Mind()
    m.tell("Ada is zorpy.")
    r = m.tell("Ada is nonzorpy.")
    assert "conflict" in r.outcome
    assert m.ask("Is Ada zorpy?").answer.value == "Conflict"


def test_er_goes_both_ways() -> None:
    m = Mind()
    m.tell("Bo zorps.")
    m.tell("Ada is a zorper.")
    m.tell("Cy zorps.")
    assert m.ask("Does Ada zorp?").answer.value == YES
    assert m.ask("Is Cy a zorper?").answer.value == YES


def test_a_dropped_e_is_undone() -> None:
    m = Mind()
    m.tell("Bo zorples.")
    assert m.tell("Ada is a zorpler.").printed.splitlines()[-1] == "note   zorpler = er + zorple"
    assert m.ask("Does Ada zorple?").answer.value == YES


def test_a_doubled_consonant_is_undone() -> None:
    m = Mind()
    m.tell("Bo glubs.")
    assert m.tell("Ada is a glubber.").printed.splitlines()[-1] == "note   glubber = er + glub"
    assert m.ask("Does Ada glub?").answer.value == YES


def test_an_i_that_stands_for_y_is_undone() -> None:
    m = Mind()
    m.tell("Bo and Cy flurry.")
    assert m.tell("Ada is flurriable.").printed.splitlines()[-1] == "note   flurriable = able + flurry"


def test_a_word_the_grammar_knows_is_never_split() -> None:
    m = Mind()
    for s in ("Ada is happy.", "Tom is a runner.", "Eve is untidy."):
        m.tell(s)
    assert m.db.execute("SELECT COUNT(*) FROM morph").fetchone()[0] == 0 and rules(m) == 0


def test_a_repeat_splits_once() -> None:
    m = Mind()
    m.tell("Ada is zorpy.")
    m.tell("Pip is nonzorpy.")
    m.tell("Bo is nonzorpy.")
    assert m.db.execute("SELECT COUNT(*) FROM morph").fetchone()[0] == 1 and rules(m) == 2

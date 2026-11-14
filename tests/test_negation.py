"""Findings A and B from manual use: negation over indefinites and bare nouns, and questions with nothing to enumerate."""

import pytest

from helpers import fixture_path
from tolk import compile as comp, lf, sem
from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


@pytest.fixture()
def mind() -> Mind:
    return Mind()


def test_negated_bare_noun_is_a_negative_rule(mind: Mind) -> None:
    r = mind.tell("Kim does not like fish.")
    assert r.printed == "rule   not _like_v_1(_, kim, X) :- _fish_n_1(X)"


def test_negated_indefinite_is_a_negative_rule(mind: Mind) -> None:
    assert mind.tell("Kim does not own a dog.").printed == "rule   not _own_v_1(_, kim, X) :- _dog_n_1(X)"


def test_negated_bare_noun_creates_nothing_and_applies_to_known_things(mind: Mind) -> None:
    mind.tell("Kim does not like fish.")
    assert mind.db.execute("SELECT COUNT(*) FROM fact WHERE pred = '_fish_n_1'").fetchone()[0] == 0
    mind.tell("Nemo is a fish.")
    assert mind.ask("Does Kim like Nemo?").answer.value == NO
    assert mind.ask("Does Kim like Rex?").answer.value == UNKNOWN


def test_negated_bare_plural_subject_is_a_negative_rule(mind: Mind) -> None:
    assert mind.tell("Dogs do not bark.").printed == "rule   not _bark_v_1(_, X) :- _dog_n_1(X)"


def test_negated_subject_indefinite_keeps_wide_scope(mind: Mind) -> None:
    assert mind.tell("A dog does not bark.").printed.startswith("tell")


def test_every_under_negation_is_refused(mind: Mind) -> None:
    r = mind.tell("Every dog does not bark.")
    assert r.outcome == "refused" and "SCOPE_AMBIGUOUS" in r.printed


def test_the_verb_reading_of_fish_loses_to_the_noun_reading() -> None:
    # Reading 1 is the verb "to fish" with its object left implicit; it says less than the noun reading.
    readings = [sem.read(r["simplemrs"]) for r in __import__("json").loads(fixture_path("Kim does not like fish.").read_text())["readings"]]
    assert "_fish_v_1" in lf.show(comp.compile_reading(readings[0]))
    k, x = comp.choose(readings, set())
    assert k > 0 and "_like_v_1" in lf.show(x)


def test_wanted_variable_in_no_atom_is_refused(mind: Mind) -> None:
    mind.tell("Kim is a person.")
    r = mind.ask("Who is Kim?")
    assert r.outcome == "refused"
    assert "UNCONSTRAINED_WANTED" in r.printed or "IDENTITY_NOT_YET" in r.printed


def test_compile_refuses_an_unconstrained_wanted_variable() -> None:
    raw = __import__("json").loads(fixture_path("Who is Kim?").read_text())["readings"][0]["simplemrs"]
    x = comp.compile_reading(sem.read(raw))
    assert isinstance(x, lf.Refusal) and x.code == "UNCONSTRAINED_WANTED"


def test_a_reading_with_an_unused_negation_does_not_compile() -> None:
    r = sem.read(__import__("json").loads(fixture_path("Kim does not like fish.").read_text())["readings"][0]["simplemrs"])
    stripped = sem.Reading(r.top, r.index, tuple(e for e in r.eps if e.pred != "_fish_v_1"), r.qeq, r.props)
    x = comp.compile_reading(stripped)
    assert isinstance(x, lf.Refusal) and x.code == "UNCONSUMED"


def test_a_reading_with_an_unused_quantified_variable_does_not_compile() -> None:
    r = sem.read(__import__("json").loads(fixture_path("Kim likes Sandy.").read_text())["readings"][0]["simplemrs"])
    stripped = sem.Reading(r.top, r.index, tuple(e for e in r.eps if e.pred != "_like_v_1"), r.qeq, r.props)
    x = comp.compile_reading(stripped)
    assert isinstance(x, lf.Refusal)

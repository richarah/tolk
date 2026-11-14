"""Phase 18: defaults and the conflict policy. The dialogue is SPEC2's. Expectations were written before the code."""

import pytest

from tolk.ask import CONFLICT, NO, UNKNOWN, YES
from tolk.mind import Mind

STORE = ["Birds fly.", "Every penguin is a bird.", "Penguins do not fly.", "Pingu is a penguin.", "Tweety is a bird."]


def make(policy: tuple[str, ...] = ("specific",), told: list[str] = STORE) -> Mind:
    m = Mind(policy=policy)
    for s in told:
        m.tell(s)
    return m


def test_printed_forms_differ_for_defaults_and_strict_rules() -> None:
    m = Mind()
    assert m.tell("Birds fly.").printed == "default _fly_v_1(E!, X) :- _bird_n_1(X)"
    assert m.tell("Every penguin is a bird.").printed == "rule   _bird_n_1(X) :- _penguin_n_1(X)"
    assert m.tell("Penguins do not fly.").printed == "default not _fly_v_1(_, X) :- _penguin_n_1(X)"
    assert m.tell("All cats purr.").printed.startswith("rule ")
    assert m.tell("No dog flies.").printed.startswith("rule ")


def test_the_dialogue() -> None:
    m = make()
    assert m.ask("Does Tweety fly?").answer.value == YES
    r = m.ask("Does Pingu fly?")
    assert r.answer.value == NO
    assert 'defeated "Birds fly." (rule 1) by specific' in r.outcome
    # With no policy nothing separates the two defaults.
    assert make(policy=()).ask("Does Pingu fly?").answer.value == CONFLICT
    r = m.tell("Tweety does not fly.")
    assert r.outcome.startswith("stored")
    r = m.ask("Does Tweety fly?")
    assert r.answer.value == NO and "told fact" in r.outcome


def test_the_more_specific_default_wins_through_a_strict_chain() -> None:
    # A bird is a creature by a strict rule, so "Birds fly." is more specific than "Creatures do not fly."
    m = make(told=["Birds fly.", "Pingu is a bird.", "Every bird is a creature.", "Creatures do not fly."])
    assert m.ask("Does Pingu fly?").answer.value == YES
    assert m.ask("Does Pingu fly?").outcome.count("defeated") == 1


def test_two_defaults_with_unrelated_bodies_are_a_conflict() -> None:
    m = make(told=["Birds fly.", "Pets do not fly.", "Pingu is a bird.", "Pingu is a pet."])
    assert m.ask("Does Pingu fly?").answer.value == CONFLICT


def test_strict_beats_default() -> None:
    m = make(told=["Birds fly.", "Pingu is a penguin.", "Every penguin is a bird.", "No penguin flies."])
    r = m.ask("Does Pingu fly?")
    assert r.answer.value == NO and "by strict rules" in r.outcome


def test_a_told_fact_against_a_strict_conclusion_is_still_refused() -> None:
    m = Mind()
    for s in ["Tweety is a robin.", "Every robin is a bird.", "Every bird flies."]:
        m.tell(s)
    assert m.tell("Tweety does not fly.").outcome.startswith("refused, contradicts")


def test_trusted_and_recent_separate_two_equally_general_defaults() -> None:
    told = ["Cats sleep.", "Cats do not sleep.", "Tom is a cat."]
    assert make(policy=("specific",), told=told).ask("Does Tom sleep?").answer.value == CONFLICT
    assert make(policy=("recent",), told=told).ask("Does Tom sleep?").answer.value == NO
    m = Mind(policy=("trusted",))
    m.tell("Cats sleep.", trust=5)
    m.tell("Cats do not sleep.")
    m.tell("Tom is a cat.")
    assert m.ask("Does Tom sleep?").answer.value == YES


def test_the_policy_list_is_applied_in_order() -> None:
    told = ["Birds fly.", "Every penguin is a bird.", "Penguins do not fly.", "Pingu is a penguin."]
    # specific first: the penguin default wins, whatever the trust of the other.
    m = Mind(policy=("specific", "trusted"))
    m.tell("Birds fly.", trust=9)
    for s in told[1:]:
        m.tell(s)
    assert m.ask("Does Pingu fly?").answer.value == NO
    m = Mind(policy=("trusted", "specific"))
    m.tell("Birds fly.", trust=9)
    for s in told[1:]:
        m.tell(s)
    assert m.ask("Does Pingu fly?").answer.value == YES


def test_changing_the_policy_rebuilds_the_derived_facts() -> None:
    m = make(policy=())
    assert m.ask("Does Pingu fly?").answer.value == CONFLICT
    m.set_policy(("specific",))
    assert m.ask("Does Pingu fly?").answer.value == NO
    assert m.db.execute("SELECT value FROM meta WHERE key = 'policy'").fetchone()[0] == "specific"


def test_an_unknown_policy_criterion_is_an_error() -> None:
    with pytest.raises(ValueError):
        Mind(policy=("loudest",))


def test_every_derived_fact_has_a_proof_after_a_rebuild() -> None:
    m = make()
    assert m.db.execute("SELECT COUNT(*) FROM fact WHERE id NOT IN (SELECT fact FROM why)").fetchone()[0] == 0


@pytest.mark.parametrize("question, value, by_default", [
    ("Is every penguin a bird?", YES, False),
    ("Is every bird a penguin?", UNKNOWN, False),
    ("Does every bird fly?", YES, True),
    ("Does every penguin fly?", NO, True),
    ("Do penguins fly?", NO, True),
    ("Is every robin a bird?", UNKNOWN, False),
])
def test_universal_questions_use_what_follows_for_a_fresh_thing(question: str, value: str, by_default: bool) -> None:
    r = make().ask(question)
    assert r.answer.value == value and r.answer.by_default == by_default
    assert r.outcome == value + (", by default" if by_default else "")


def test_known_instances_are_not_evidence_for_every() -> None:
    m = Mind()
    for s in ["Tweety is a bird.", "Sparrow is a bird.", "Tweety flies.", "Sparrow flies.", "Pip is a bird.", "Pip flies."]:
        m.tell(s)
    assert m.ask("Does every bird fly?").answer.value == UNKNOWN

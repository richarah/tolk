"""Phase 19: revision. The dialogue is SPEC2's. Expectations were written before the code."""

import pytest

from tolk.ask import CONFLICT, NO, UNKNOWN, YES
from tolk.mind import Mind

TIER_A = [
    "Tweety is a robin.", "Every robin is a bird.", "Every bird flies.", "Birds are animals.",
    "Tweety sings.", "Every robin that sings is happy.", "Kim is a person.", "Kim owns a dog.",
    "Every person who owns a dog is happy.", "Kim likes Sandy.", "Rex is a dog.", "Every dog has an owner.",
]
CONFLICTED = TIER_A + ["Pingu is a penguin.", "Pingu does not fly.", "Every penguin is a bird."]


def tier_b(**settings) -> Mind:
    m = Mind(**settings)
    for s in CONFLICTED:
        m.tell(s)
    return m


def test_diagnose_lists_the_four_sentences_weakest_first() -> None:
    m = tier_b()
    assert m.ask("Does Pingu fly?").answer.value == CONFLICT
    (d,) = m.diagnose()
    assert [c.text for c in d.candidates] == ["Every penguin is a bird.", "Every bird flies.", "Pingu does not fly.", "Pingu is a penguin."]
    assert [c.kind for c in d.candidates] == ["strict", "strict", "told", "told"]


def test_the_dialogue() -> None:
    m = tier_b()
    r = m.tell("Forget that every bird flies.")
    assert r.outcome == 'forgot "Every bird flies."'
    assert m.ask("Does Pingu fly?").answer.value == NO
    assert m.ask("Does Tweety fly?").answer.value == UNKNOWN


def test_the_retracted_sentence_stays_with_its_reason() -> None:
    m = tier_b()
    m.tell("Forget that every bird flies.")
    (sid, text) = m.db.execute("SELECT id, text FROM sentence WHERE text = 'Every bird flies.'").fetchone()
    assert m.db.execute("SELECT reason FROM revision WHERE sentence = ?", (sid,)).fetchone()[0] == "forget that every bird flies."
    assert m.db.execute("SELECT COUNT(*) FROM rule WHERE sentence = ?", (sid,)).fetchone()[0] == 0
    assert m.tell("Every bird flies.").outcome.startswith("rule stored")  # no longer in force, so not a repeat
    assert m.ask("Does Pingu fly?").answer.value == CONFLICT


def test_with_auto_revise_off_a_conflict_is_reported_with_its_candidates() -> None:
    m = Mind()
    for s in ["Tweety is a robin.", "Every robin is a bird.", "Every bird flies."]:
        m.tell(s)
    r = m.observe("Tweety does not fly.")
    assert r.outcome.startswith("stored")
    assert "conflict: fly(tweety) against not fly(tweety)" in r.outcome and "Every bird flies." in r.outcome
    assert "Tweety does not fly." not in r.outcome.split("removing:")[1]
    assert m.ask("Does Tweety fly?").answer.value == CONFLICT


def test_with_auto_revise_on_the_weakest_candidate_that_is_not_an_observation_goes() -> None:
    m = Mind(auto_revise=True)
    for s in ["Tweety is a robin.", "Every robin is a bird.", "Every bird flies."]:
        m.tell(s)
    r = m.observe("Tweety does not fly.")
    assert 'retracted "Every bird flies." to end a conflict' in r.outcome
    assert m.ask("Does Tweety fly?").answer.value == NO
    assert m.db.execute("SELECT COUNT(*) FROM conflict").fetchone()[0] == 0


def test_a_plain_tell_that_contradicts_a_strict_conclusion_is_still_refused_with_auto_revise() -> None:
    m = Mind(auto_revise=True)
    for s in ["Tweety is a robin.", "Every robin is a bird.", "Every bird flies."]:
        m.tell(s)
    assert m.tell("Tweety does not fly.").outcome.startswith("refused, contradicts")


def test_defaults_are_removed_before_strict_rules_before_told_facts() -> None:
    m = Mind(policy=())
    for s in ["Birds fly.", "Every robin is a bird.", "Robins do not fly.", "Tweety is a robin."]:
        m.tell(s)
    (d,) = m.diagnose()
    assert [c.kind for c in d.candidates] == ["default", "default", "strict", "told"]


def test_trust_and_recency_order_the_candidates_within_a_kind() -> None:
    m = Mind()
    m.tell("Tom is a cat.", trust=5)
    m.tell("Every cat purrs.", trust=1)
    m.tell("Every cat is a pet.", trust=3)
    m.tell("No pet purrs.", trust=3)
    d = m.diagnose()[0]
    strict = [(c.trust, c.text) for c in d.candidates if c.kind == "strict"]
    assert strict == sorted(strict, key=lambda t: t[0])  # lower trust first
    assert strict[0] == (1, "Every cat purrs.")


def test_an_identity_cannot_be_retracted() -> None:
    m = Mind()
    m.tell("Clark Kent is Superman.")
    sid = m.db.execute("SELECT id FROM sentence").fetchone()[0]
    with pytest.raises(ValueError):
        m.retract(sid)
    assert m.hear("Forget that Clark Kent is Superman.").outcome.startswith("refused")


def test_forgetting_what_was_never_told_changes_nothing() -> None:
    m = Mind()
    m.tell("Rio is a sparrow.")
    assert m.hear("Forget that Rio is a finch.").outcome == "nothing that was told means that"
    assert m.ask("Is Rio a sparrow?").answer.value == YES


def test_forget_removes_the_most_recent_matching_sentence_only() -> None:
    m = Mind()
    m.tell("Rio is a sparrow.")
    m.suppose("Rio is a sparrow")  # a repeat in force: stores nothing, so there is only one told sentence
    m.drop()
    assert m.hear("Forget that Rio is a sparrow.").outcome == 'forgot "Rio is a sparrow."'
    assert m.ask("Is Rio a sparrow?").answer.value == UNKNOWN


def test_the_settings_are_stored_with_the_facts() -> None:
    m = Mind(policy=("specific", "recent"), auto_revise=True)
    assert m.auto_revise and m.policy == ("specific", "recent")
    assert not Mind().auto_revise

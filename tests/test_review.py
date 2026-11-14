"""Findings from the review. Each test failed before its fix."""

import json

import pytest

from helpers import fixture_path
from tolk import compile as comp, lf, sem
from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


@pytest.fixture()
def mind() -> Mind:
    return Mind()


def refused(r, code: str) -> bool:
    return r.outcome == "refused" and code in r.printed


def test_a_refusal_for_a_meaning_is_not_overridden_by_a_lower_reading(mind: Mind) -> None:
    # Reading 2 of "Nobody flies." is the real one, and it is unsupported; reading 3 reads Nobody as a name.
    assert refused(mind.tell("Nobody flies."), "UNSUPPORTED_PREDICATE")
    # Phase 12 lifted the negated-question refusal; what matters is that the question is read as a question about dogs.
    assert mind.tell("Which dog does not bark?").printed == "ask X  _dog_n_1(X), not _bark_v_1(E, X)"
    assert mind.db.execute("SELECT COUNT(*) FROM fact").fetchone()[0] == 0


def test_or_is_not_stored_as_and(mind: Mind) -> None:
    assert refused(mind.tell("Every dog barks or sleeps."), "COORDINATION")
    assert mind.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0] == 0


def test_and_between_clauses_stores_each_clause_and_no_fact_about_events(mind: Mind) -> None:
    # Phase 15 replaced the refusal: each clause is stored on its own event, and the connective is not a fact.
    mind.tell("Kim sings and dances.")
    assert {p for (p,) in mind.db.execute("SELECT pred FROM fact")} == {"_sing_v_1", "_dance_v_1"}


@pytest.mark.parametrize("text", ["Kim will sing.", "Kim is singing.", "Kim has arrived."])
def test_tense_and_aspect_that_are_not_stored_are_refused(mind: Mind, text: str) -> None:
    r = mind.tell(text)
    assert r.outcome == "refused" and ("TENSE" in r.printed or "ASPECT" in r.printed)
    assert mind.db.execute("SELECT COUNT(*) FROM fact").fetchone()[0] == 0


def test_a_past_tense_in_a_relative_clause_is_not_dropped(mind: Mind) -> None:
    r = mind.tell("Every person who owned a dog is happy.")
    assert r.outcome == "refused"


def test_a_universal_question_is_not_answered_from_known_instances(mind: Mind) -> None:
    # Phase 18 answers it, by what follows for a fresh dog. A dog that is a mammal is not evidence for "every dog".
    mind.tell("Rex is a dog.")
    mind.tell("Rex is a mammal.")
    assert mind.ask("Is every dog a mammal?").answer.value == UNKNOWN


def test_a_merge_leaves_no_proof_with_a_missing_premise(mind: Mind) -> None:
    for s in ["Zed is a dog.", "Zed flies.", "Every dog that flies is happy.", "Tweety is a dog.", "Tweety flies.", "Tweety is Zed."]:
        mind.tell(s)
    db = mind.db
    for fact, premises in db.execute("SELECT fact, premises FROM why").fetchall():
        for p in json.loads(premises):
            assert db.execute("SELECT 1 FROM fact WHERE id = ?", (p,)).fetchone(), (fact, p)


def test_dropping_a_supposition_restores_every_table(mind: Mind) -> None:
    def dump():
        return {t: sorted(mind.db.execute(f"SELECT * FROM {t}").fetchall())
                for t in ("sentence", "entity", "name", "fact", "why", "rule", "merge", "conflict")}
    for s in ["Tweety is a robin.", "Every robin is a bird.", "Every bird flies.", "Pingu is a penguin.", "Pingu does not fly.", "Every penguin is a bird."]:
        mind.tell(s)
    before = dump()
    mind.suppose("Tweety is a penguin.")
    mind.drop()
    assert dump() == before


@pytest.mark.parametrize("text, pred", [("Kim can sing.", "_can_v_modal"), ("Kim must sing.", "_must_v_modal")])
def test_a_modal_is_refused_by_name_not_as_a_variable(mind: Mind, text: str, pred: str) -> None:
    r = mind.tell(text)
    assert r.outcome == "refused" and r.printed == f"refuse UNSUPPORTED_PREDICATE: {pred}"


def test_a_repeat_is_by_meaning_not_by_text(mind: Mind) -> None:
    mind.tell("Kim owns a dog.")
    r = mind.tell("Kim owns a dog")
    assert r.outcome == 'already told: "Kim owns a dog."'
    assert mind.db.execute("SELECT COUNT(*) FROM fact WHERE pred = '_dog_n_1'").fetchone()[0] == 1


def test_a_repeated_rule_is_not_stored_twice(mind: Mind) -> None:
    mind.tell("Every robin is a bird.")
    assert mind.tell("Every robin is a bird").outcome.startswith("already told")
    assert mind.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0] == 1


def test_a_dropped_supposition_is_no_longer_in_force(mind: Mind) -> None:
    mind.suppose("Tweety is a penguin.")
    mind.drop()
    assert mind.suppose("Tweety is a penguin.").outcome.startswith("stored")


def _prepositions_store():
    from tolk import lf, store
    from tolk.lf import Atom, Const
    db = store.open_store()
    sid = store.add_sentence(db, "synthetic")
    store.tell(db, lf.Tell((Atom("_work_v_1", (Const("e1", "event"), Const("sam"))), Atom("_in_p_loc", (Const("e1", "event"), Const("oslo"))))), sid)
    return db


def _ask_in(db, prep: str):
    from tolk import ask, lf
    from tolk.lf import Atom, Const, Var
    return ask.answer(db, lf.Ask((Atom("_work_v_1", (Var("e"), Const("sam"))), Atom(prep, (Var("e"), Const("oslo")))), ()))


def test_a_preposition_sense_is_widened_only_when_nothing_matches_exactly() -> None:
    db = _prepositions_store()
    wide = _ask_in(db, "_in_p_state")
    assert wide.value == YES and wide.widened == ("_in_p_state matched as _in_p_loc",)
    exact = _ask_in(db, "_in_p_loc")
    assert exact.value == YES and exact.widened == ()


def test_a_preposition_with_another_lemma_is_not_widened() -> None:
    assert _ask_in(_prepositions_store(), "_on_p_state").value == UNKNOWN

"""Tier B: the dialogue table in SPEC.md, run in order through Mind."""

import pytest

from tolk import engine, lf, store
from tolk.ask import CONFLICT, NO, YES
from tolk.lf import Atom, Const, Var
from tolk.mind import Mind

TIER_A = [
    "Tweety is a robin.", "Every robin is a bird.", "Every bird flies.", "Birds are animals.",
    "Tweety sings.", "Every robin that sings is happy.", "Kim is a person.", "Kim owns a dog.",
    "Every person who owns a dog is happy.", "Kim likes Sandy.", "Rex is a dog.", "Every dog has an owner.",
]


@pytest.fixture(scope="module")
def mind() -> Mind:
    m = Mind()
    for s in TIER_A:
        m.tell(s)
    return m


def test_pingu_is_stored(mind: Mind) -> None:
    assert mind.tell("Pingu is a penguin.").outcome.startswith("stored")


def test_negative_fact_is_stored(mind: Mind) -> None:
    r = mind.tell("Pingu does not fly.")
    assert r.outcome.startswith("stored")
    assert mind.db.execute("SELECT COUNT(*) FROM fact WHERE pred = '_fly_v_1' AND positive = 0 AND a1 = 'pingu'"
                           ).fetchone()[0] == 1


def test_does_pingu_fly_is_no(mind: Mind) -> None:
    r = mind.ask("Does Pingu fly?")
    assert r.answer.value == NO


def test_every_penguin_is_a_bird_records_a_conflict(mind: Mind) -> None:
    assert mind.tell("Every penguin is a bird.").outcome == "rule stored"
    conflicts = mind.db.execute("SELECT COUNT(*) FROM conflict").fetchone()[0]
    assert conflicts == 1


def test_does_pingu_fly_is_conflict_with_both_proofs(mind: Mind) -> None:
    r = mind.ask("Does Pingu fly?")
    assert r.answer.value == CONFLICT
    assert len(r.answer.proofs) == 2 and all(r.answer.proofs)


def test_clark_kent_is_superman_is_one_thing(mind: Mind) -> None:
    r = mind.tell("Clark Kent is Superman.")
    assert r.outcome.startswith("one thing")
    assert mind.db.execute("SELECT COUNT(*) FROM merge").fetchone()[0] == 1


def test_superman_flies_is_stored(mind: Mind) -> None:
    assert mind.tell("Superman flies.").outcome.startswith("stored")


def test_does_clark_kent_fly_is_yes(mind: Mind) -> None:
    assert mind.ask("Does Clark Kent fly?").answer.value == YES


def test_the_robin_is_happy_is_yes(mind: Mind) -> None:
    assert mind.ask("Is the robin happy?").answer.value == YES


def test_the_dog_barks_is_refused_with_count(mind: Mind) -> None:
    r = mind.tell("The dog barks.")
    assert r.outcome == "refused"
    assert "DEFINITE_MATCHES: 2 known things match" in r.printed


def test_tweety_does_not_fly_is_refused_with_proof(mind: Mind) -> None:
    r = mind.tell("Tweety does not fly.")
    assert r.outcome.startswith("refused, contradicts")
    assert "fly(tweety)" in r.outcome


def test_negation_as_failure_in_a_rule_body() -> None:
    # Every thing that is a robin and does not fly is a sparrow-like one. Without a stored flying, it is.
    db_mind = Mind()
    sid = store.add_sentence(db_mind.db, "synthetic")
    store.tell(db_mind.db, lf.Tell((Atom("robin", (Const("tweety"),)),)), sid)
    rule = lf.Rule(
        (Atom("grounded", (Var("x"),)),),
        (Atom("robin", (Var("x"),)), Atom("fly", (Var("e"), Var("x")), positive=False)),
    )
    assert engine.check(db_mind.db, rule) is None
    store.add_rule(db_mind.db, rule, sid)
    engine.run(db_mind.db)
    assert db_mind.db.execute("SELECT COUNT(*) FROM fact WHERE pred = 'grounded'").fetchone()[0] == 1


def test_negated_variable_must_be_bound_positively() -> None:
    rule = lf.Rule((Atom("p", (Var("x"),)),), (Atom("q", (Var("y"),), positive=False),))
    assert engine.check(store.open_store(), rule) == lf.Refusal("UNSAFE_NEGATION", "y")


def test_negation_through_its_own_head_is_refused() -> None:
    db = store.open_store()
    sid = store.add_sentence(db, "synthetic")
    rule = lf.Rule((Atom("p", (Var("x"),)),), (Atom("q", (Var("x"),)), Atom("p", (Var("x"),), positive=False)))
    store.add_rule(db, rule, sid)
    assert engine.check(db, rule) == lf.Refusal("NEGATION_CYCLE", "p")

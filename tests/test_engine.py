import time

from tolk import engine, negation, lf, store
from tolk.mind import Mind
from tolk.lf import Atom, Const, Var

TIER_A_STATEMENTS = [
    "Tweety is a robin.", "Every robin is a bird.", "Every bird flies.", "Birds are animals.",
    "Tweety sings.", "Every robin that sings is happy.", "Kim is a person.", "Kim owns a dog.",
    "Every person who owns a dog is happy.", "Kim likes Sandy.", "Rex is a dog.", "Every dog has an owner.",
]


def count(db, pred: str, value: str, column: str = "a0") -> int:
    return db.execute(f"SELECT COUNT(*) FROM fact WHERE pred = ? AND {column} = ?", (pred, value)).fetchone()[0]


def test_tier_a_statements_derive_expected_facts() -> None:
    mind = Mind()
    for s in TIER_A_STATEMENTS:
        mind.tell(s)
    db = mind.db
    assert count(db, "_bird_n_1", "tweety") == 1
    assert count(db, "_animal_n_1", "tweety") == 1
    assert count(db, "_fly_v_1", "tweety", "a1") == 1
    assert count(db, "_happy_a_with", "tweety", "a1") == 1
    assert count(db, "_happy_a_with", "kim", "a1") == 1
    assert count(db, "_have_v_1", "rex", "a1") == 1
    assert db.execute("SELECT COUNT(*) FROM entity WHERE kind = 'skolem'").fetchone()[0] >= 2


def test_telling_the_same_statement_twice_adds_nothing() -> None:
    mind = Mind()
    mind.tell("Kim likes Sandy.")
    db = mind.db
    before = db.execute("SELECT COUNT(*) FROM fact").fetchone()[0]
    mind.tell("Kim likes Sandy.")
    assert db.execute("SELECT COUNT(*) FROM fact").fetchone()[0] == before


def test_dog_owner_is_created_once_and_rerun_creates_none() -> None:
    mind = Mind()
    mind.tell("Rex is a dog.")
    mind.tell("Every dog has an owner.")
    db = mind.db
    owners = db.execute("SELECT COUNT(*) FROM fact WHERE pred = '_owner_n_of'").fetchone()[0]
    assert owners == 1
    assert engine.run(db) == 0
    assert db.execute("SELECT COUNT(*) FROM fact WHERE pred = '_owner_n_of'").fetchone()[0] == 1


def test_recursion_through_skolem_terms_stops() -> None:
    # Each person gets a new parent, and each parent is a person. Without the guard this never ends.
    db = store.open_store()
    sid = store.add_sentence(db, "synthetic")
    store.tell(db, lf.Tell((Atom("person", (Const("kim"),)),)), sid)
    store.add_rule(db, lf.Rule(
        (Atom("has", (Var("e"), Var("x"), Var("p"))), Atom("parent", (Var("p"),))),
        (Atom("person", (Var("x"),)),),
    ), sid)
    store.add_rule(db, lf.Rule((Atom("person", (Var("x"),)),), (Atom("parent", (Var("x"),)),)), sid)
    engine.run(db)
    assert db.execute("SELECT COUNT(*) FROM fact WHERE pred = 'parent'").fetchone()[0] == 1


def test_fifty_thousand_facts_through_six_rules_reach_fixpoint() -> None:
    db = store.open_store()
    sid = store.add_sentence(db, "synthetic")
    atoms = tuple(Atom("p0", (Const(f"c{i}"),)) for i in range(50_000))
    store.tell(db, lf.Tell(atoms), sid)
    for i in range(6):
        store.add_rule(db, lf.Rule((Atom(f"p{i + 1}", (Var("x"),)),), (Atom(f"p{i}", (Var("x"),)),)), sid)
    start = time.perf_counter()
    added = engine.run(db)
    elapsed = time.perf_counter() - start
    print(f"\nfixpoint: {added} derived facts in {elapsed:.2f}s")
    assert added == 6 * 50_000
    assert engine.run(db) == 0


def test_a_negated_atom_derived_in_a_later_round_blocks_the_rule() -> None:
    # r(x) :- s(x), not q2(x) is told first. q2 is only derived in round 2, through q1. Strata run the negated rule last.
    db = store.open_store()
    sid = store.add_sentence(db, "synthetic")
    x = Var("x")
    store.add_rule(db, lf.Rule((Atom("r", (x,)),), (Atom("s", (x,)), Atom("q2", (x,), positive=False))), sid)
    store.add_rule(db, lf.Rule((Atom("q1", (x,)),), (Atom("p", (x,)),)), sid)
    store.add_rule(db, lf.Rule((Atom("q2", (x,)),), (Atom("q1", (x,)),)), sid)
    store.tell(db, lf.Tell((Atom("p", (Const("a"),)), Atom("s", (Const("a"),)), Atom("s", (Const("b"),)))), sid)
    engine.run(db)
    assert db.execute("SELECT a0 FROM fact WHERE pred = 'r'").fetchall() == [("b",)]
    assert engine.run(db) == 0


def test_a_cycle_through_negation_is_refused_when_the_rule_is_told() -> None:
    db = store.open_store()
    sid = store.add_sentence(db, "synthetic")
    x = Var("x")
    store.add_rule(db, lf.Rule((Atom("p", (x,)),), (Atom("q", (x,)), Atom("r", (x,), positive=False))), sid)
    closing = lf.Rule((Atom("r", (x,)),), (Atom("p", (x,)),))
    assert negation.check(db, closing).code == "NEGATION_CYCLE"

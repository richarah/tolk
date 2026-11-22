"""Medium item M4: negation as failure is evaluated stratum by stratum, each stratum to fixpoint, before any rule that negates what it derives.
The rule that negates is listed first, so a round-by-round evaluation would derive from it before the chain it negates has finished."""

from tolk import engine, lf, store
from tolk.lf import Atom, Const, Var


def store_with(rules: list[lf.Rule], facts: list[Atom]):
    db = store.open_store()
    sid = store.add_sentence(db, "synthetic")
    for r in rules:
        store.add_rule(db, r, sid)
    store.tell(db, lf.Tell(tuple(facts)), sid)
    return db


def x() -> Var:
    return Var("x")


def chain_rules() -> list[lf.Rule]:
    flag = lf.Rule((Atom("flag", (x(),)),), (Atom("thing", (x(),)), Atom("p3", (x(),), False)))  # negates the top of the chain
    p1 = lf.Rule((Atom("p1", (x(),)),), (Atom("q", (x(),)),))
    p2 = lf.Rule((Atom("p2", (x(),)),), (Atom("p1", (x(),)),))
    p3 = lf.Rule((Atom("p3", (x(),)),), (Atom("p2", (x(),)),))
    return [flag, p1, p2, p3]


def test_a_negated_chain_is_not_used_before_the_chain_is_complete() -> None:
    db = store_with(chain_rules(), [Atom("thing", (Const("a", "named"),)), Atom("q", (Const("a", "named"),))])
    engine.run(db)
    assert {p for (p,) in db.execute("SELECT pred FROM fact")} == {"thing", "q", "p1", "p2", "p3"}


def test_the_chain_without_its_last_link_makes_the_negated_rule_fire() -> None:
    db = store_with(chain_rules(), [Atom("thing", (Const("a", "named"),)), Atom("q", (Const("b", "named"),))])
    engine.run(db)
    assert db.execute("SELECT COUNT(*) FROM fact WHERE pred = 'flag' AND a0 = 'a'").fetchone()[0] == 1


def test_the_strata_are_in_order_and_the_negated_rule_is_above_the_chain() -> None:
    rules = chain_rules()
    level = __import__("tolk.negation", fromlist=["strata"]).strata(rules)
    assert level[0] > max(level[1:])
    assert level[1:] == [0, 0, 0]


def test_a_cycle_through_negation_is_refused_when_stored() -> None:
    from tolk import negation
    loop = lf.Rule((Atom("p", (x(),)),), (Atom("thing", (x(),)), Atom("p", (x(),), False)))
    try:
        negation.strata([loop])
    except ValueError:
        return
    raise AssertionError("a rule that negates its own head has no stratum")

"""Proposals: a pair of one-place predicates P and Q where every known P is a Q, and Q has more. Nothing is stored unless confirmed."""

from tolk.mind import Mind


def robins_and_birds(birds: list[str], robins: list[str]) -> Mind:
    m = Mind()
    for name in robins:
        m.tell(f"{name} is a robin.")
    for name in birds:
        m.tell(f"{name} is a bird.")
    return m


FOUR = ["Tweety", "Kim", "Rex", "Ali"]


def test_four_things_sharing_two_predicates_give_one_proposal() -> None:
    m = robins_and_birds(FOUR + ["Zed"], FOUR)
    proposals = m.propose()
    assert len(proposals) == 1
    assert proposals[0].question == "Is every robin a bird?"


def test_a_counterexample_gives_no_proposal() -> None:
    # Ali is a robin but not known to be a bird, so no robin-to-bird rule is supported.
    m = robins_and_birds(["Tweety", "Kim", "Rex", "Zed"], FOUR)
    assert m.propose() == []


def test_nothing_is_stored_before_confirm() -> None:
    m = robins_and_birds(FOUR + ["Zed"], FOUR)
    rules = m.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0]
    facts = m.db.execute("SELECT COUNT(*) FROM fact").fetchone()[0]
    m.propose()
    assert m.db.execute("SELECT COUNT(*) FROM rule").fetchone()[0] == rules
    assert m.db.execute("SELECT COUNT(*) FROM fact").fetchone()[0] == facts


def test_confirmed_proposal_is_stored_and_no_longer_proposed() -> None:
    m = robins_and_birds(FOUR + ["Zed"], FOUR)
    [proposal] = m.propose()
    assert m.confirm(proposal).outcome == "rule stored"
    assert m.propose() == []
    m.tell("Milo is a robin.")
    assert m.ask("Is Milo a bird?").answer.value == "Yes"

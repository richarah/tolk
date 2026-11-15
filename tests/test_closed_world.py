"""Item 2: a closed-world setting, stored in meta, default off."""

from tolk.mind import Mind


def test_it_is_off_by_default_and_unknown_stays_the_answer() -> None:
    m = Mind()
    assert m.closed_world is False
    m.tell("Tweety is a bird.")
    assert m.ask("Does Tweety sing?").outcome == "Unknown"
    assert m.ask("Who sings?").outcome == "Unknown"


def test_on_a_yes_no_question_without_support_is_no() -> None:
    m = Mind(closed_world=True)
    m.tell("Tweety is a bird.")
    assert m.ask("Is Tweety a bird?").outcome.startswith("Yes")
    assert m.ask("Is Tweety a fish?").outcome == "No"
    assert m.ask("Does Tweety sing?").outcome == "No"


def test_on_a_wh_question_without_support_returns_nothing() -> None:
    m = Mind(closed_world=True)
    m.tell("Tweety sings.")
    assert m.ask("Who sings?").outcome.startswith("Tweety")
    assert m.ask("Who swims?").outcome == "Nothing"
    assert m.ask("Who swims?").answer.solutions == ()


def test_the_setting_is_kept_in_meta_and_can_change_during_a_session() -> None:
    m = Mind()
    m.set_closed_world(True)
    assert m.db.execute("SELECT value FROM meta WHERE key = 'closed_world'").fetchone() == ("1",)
    assert m.ask("Does Tweety sing?").outcome == "No"
    m.set_closed_world(False)
    assert m.ask("Does Tweety sing?").outcome == "Unknown"


def test_a_negative_fact_is_still_no_with_its_proof_and_a_conflict_stays_a_conflict() -> None:
    m = Mind(closed_world=True)
    m.tell("Tweety does not sing.")
    assert m.ask("Does Tweety sing?").outcome.startswith("No\n")


def test_a_negated_question_with_no_fact_either_way_is_yes_when_the_world_is_closed() -> None:
    m = Mind(closed_world=True)
    m.tell("Kim owns Rex.")
    assert m.ask("Does Kim not own Fido?").outcome == "Yes"
    assert m.ask("Does Kim not own Rex?").outcome.startswith("No")
    open_ = Mind()
    open_.tell("Kim owns Rex.")
    assert open_.ask("Does Kim not own Fido?").outcome == "Unknown"


def test_a_wh_question_with_a_negation_finds_the_things_with_no_such_fact() -> None:
    m = Mind(closed_world=True)
    for s in ("Rex is a dog.", "Fido is a dog.", "Spot is a dog.", "Kim owns Rex."):
        m.tell(s)
    r = m.ask("Which dogs does Kim not own?")
    assert r.answer.solutions == (("fido",), ("spot",))
    assert r.outcome.splitlines()[0] == "Fido and Spot"

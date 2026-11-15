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

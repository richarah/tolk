"""A store file can be reopened: the facts, rules, sentences and settings are there, and a supposition left open is dropped.
Written before the change; reopening a file used to fail with "table sentence already exists"."""

from tolk.mind import Mind


def test_a_stored_fact_is_there_after_reopen(tmp_path) -> None:
    path = str(tmp_path / "s.db")
    m = Mind(path)
    m.tell("Kim owns a dog.")
    m.db.commit()
    again = Mind(path)
    assert again.ask("Does Kim own a dog?").answer.value == "Yes"


def test_a_repeat_after_reopen_is_already_told(tmp_path) -> None:
    path = str(tmp_path / "s.db")
    Mind(path).tell("Every bird flies.")
    m = Mind(path)
    assert m.tell("Every bird flies.").outcome.startswith("already told")


def test_settings_are_kept_on_reopen(tmp_path) -> None:
    path = str(tmp_path / "s.db")
    m = Mind(path, closed_world=True, wording="template")
    m.db.commit()
    again = Mind(path)
    assert again.closed_world and again.wording == "template"


def test_a_supposition_left_open_is_dropped_on_reopen(tmp_path) -> None:
    path = str(tmp_path / "s.db")
    m = Mind(path)
    m.tell("Kim owns a dog.")
    m.suppose("Lee owns a cat.")
    m.db.commit()
    again = Mind(path)
    assert again.ctx == "world"
    assert again.ask("Does Lee own a cat?").answer.value == "Unknown"
    assert again.db.execute("SELECT COUNT(*) FROM fact WHERE ctx != 'world'").fetchone()[0] == 0


def test_a_supposition_after_reopen_works_and_drops_cleanly(tmp_path) -> None:
    path = str(tmp_path / "s.db")
    m = Mind(path)
    m.tell("Kim owns a dog.")
    m.suppose("Lee owns a cat.")
    m.drop()
    m.db.commit()
    again = Mind(path)
    again.suppose("Pip owns a cat.")
    assert again.ask("Does Pip own a cat?").answer.value == "Yes"
    again.drop()
    assert again.ask("Does Pip own a cat?").answer.value == "Unknown"
    assert again.ask("Does Kim own a dog?").answer.value == "Yes"

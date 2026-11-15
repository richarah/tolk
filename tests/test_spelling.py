"""Housekeeping item 6: spelling. The dialogue is the task's; the ten own-word cases were written, with their expectations, before the first run."""

import pytest

from tolk import spelling
from tolk.mind import Mind


def test_the_distance_counts_a_swap_of_adjacent_letters_as_one_and_is_written_once() -> None:
    assert spelling.distance("tweety", "twety") == 1
    assert spelling.distance("robin", "robbin") == 1
    assert spelling.distance("teh", "the") == 1
    assert spelling.distance("abcdef", "badcfe") == 3
    assert spelling.distance("", "abc") == 3 and spelling.distance("kitten", "sitting") == 3
    import pathlib
    owners = [p.name for p in pathlib.Path(spelling.__file__).parent.rglob("*.py") if "def distance" in p.read_text()]
    assert owners == ["spelling.py"]


def test_the_dialogue() -> None:
    m = Mind()
    m.tell("Tweety is a robin.")
    r = m.hear("Twety sings.")
    assert r.outcome == "refused" and r.printed == "refuse POSSIBLE_TYPO: twety: did you mean tweety?"
    assert m.db.execute("SELECT COUNT(*) FROM fact WHERE pred = '_sing_v_1'").fetchone() == (0,)
    assert m.db.execute("SELECT COUNT(*) FROM entity WHERE id = 'twety'").fetchone() == (0,)
    again = m.hear("Twety sings.")
    assert again.outcome.startswith("stored") and again.printed == "tell   _sing_v_1(e1, twety)"
    assert m.db.execute("SELECT COUNT(*) FROM entity WHERE id = 'twety'").fetchone() == (1,)


def test_the_robbin_the_tweedy_and_kim() -> None:
    m = Mind()
    m.tell("Tweety is a robin.")
    assert m.hear("Tweety is a robbin.").printed == "refuse POSSIBLE_TYPO: robbin: did you mean robin?"
    assert m.hear("Tweedy sings.").printed == "refuse POSSIBLE_TYPO: tweedy: did you mean tweety?"
    assert m.hear("Kim sings.").outcome.startswith("stored")


def test_only_the_very_next_input_confirms() -> None:
    m = Mind()
    m.tell("Tweety is a robin.")
    m.hear("Twety sings.")
    m.hear("Kim sings.")  # something else in between
    assert m.hear("Twety sings.").outcome == "refused"
    assert m.hear("Twety sings.").outcome.startswith("stored")


def test_the_table_keeps_every_name_and_surface_word_with_what_it_mapped_to() -> None:
    m = Mind()
    m.tell("Tweety is a robin.")
    rows = set(m.db.execute("SELECT word, kind, maps_to FROM spelling"))
    assert {("tweety", "name", "tweety"), ("robin", "word", "_robin_n_1")} <= rows


def test_a_refused_sentence_adds_nothing_to_the_table() -> None:
    m = Mind()
    m.tell("Tweety is a robin.")
    m.hear("Twety sings.")
    assert m.db.execute("SELECT COUNT(*) FROM spelling WHERE word = 'twety'").fetchone() == (0,)


def test_a_question_with_a_near_name_is_refused_before_it_is_answered() -> None:
    m = Mind()
    m.tell("Tweety is a robin.")
    assert m.hear("Is Twety a robin?").printed == "refuse POSSIBLE_TYPO: twety: did you mean tweety?"


# Ten own-word cases. Each: what is told, the sentence, the expected printed form (written first).
CASES = [
    (["Zorbulon is a quib."], "Zorbulan sings.", "refuse POSSIBLE_TYPO: zorbulan: did you mean zorbulon?"),  # 1: 8 letters, one substitution
    (["Glorpington is a wug."], "Glorpingtun is a quib.", "refuse POSSIBLE_TYPO: glorpingtun: did you mean glorpington?"),  # 2: a long invented name
    (["Quibble is a wug."], "Quibbel sings.", "refuse POSSIBLE_TYPO: quibbel: did you mean quibble?"),  # 3: a swap of adjacent letters
    (["Rex is a dog."], "Rexx is a dog.", None),  # 4: four letters, but nothing known within one edit except rex (3 letters): rexx is 1 away: refused
    (["Ben is a dog."], "Benn is a dog.", None),  # 5: as 4
    (["Veronika is a dog."], "Veronica is a dog.", "refuse POSSIBLE_TYPO: veronica: did you mean veronika?"),  # 6
    (["Pip is a glorb."], "Pip glorbs.", "stored"),  # 7: a form of a remembered word is not a typo
    (["Tweety is a robin."], "Tweety sings.", "stored"),  # 8: a known name
    (["Tweety is a robin."], "Wugwump is a dog.", "stored"),  # 9: nothing known is close
    (["Mimsyness is a quib."], "Quibble is a wug.", "stored"),  # 10: ten letters but nothing within two
]


@pytest.mark.parametrize("told, text, want", CASES, ids=[f"{n + 1}" for n in range(len(CASES))])
def test_own_word_case(told: list[str], text: str, want: str | None) -> None:
    m = Mind()
    for s in told:
        m.tell(s)
    r = m.hear(text)
    if want is None:
        want = f"refuse POSSIBLE_TYPO: {text.split()[0].lower()}: did you mean {told[0].split()[0].lower()}?"
    if want == "stored":
        assert r.outcome.startswith("stored"), (r.printed, r.outcome)
    else:
        assert r.printed == want and r.outcome == "refused"

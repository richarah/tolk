"""Item 3: ten invented words, each stored with the right class or refused UNKNOWN_WORD; never stored as a name."""

import sys

import pytest

from helpers import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import word_table  # noqa: E402

ROWS = word_table.run()


@pytest.mark.parametrize("row", ROWS, ids=[r[0] for r in ROWS])
def test_the_word_is_stored_with_the_right_class_or_refused_for_being_unknown(row: tuple) -> None:
    word, text, result, pos, ok = row
    assert ok, f"{text!r} gave {result}"


def test_a_lowercase_word_the_grammar_has_only_as_a_name_is_refused_not_stored_as_one() -> None:
    from tolk.mind import Mind
    m = Mind()
    r = m.tell("Tweety is a tove.")
    assert r.printed == "refuse UNKNOWN_WORD: tove" and r.outcome == "refused"
    assert m.db.execute("SELECT COUNT(*) FROM fact").fetchone()[0] == 0

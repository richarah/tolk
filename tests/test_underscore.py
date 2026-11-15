"""A word with an underscore (a column name) made the parser's meaning structure undecodable and raised. It is refused as an unknown word."""

import tolk
from tolk.mind import Mind


def test_a_word_with_an_underscore_is_refused_not_raised() -> None:
    assert tolk.printed(tolk.read("Pip is a section_name.")) == "refuse UNKNOWN_WORD: section_name"
    r = Mind().hear("List the section_name in reversed lexicographical order.")
    assert r.outcome == "refused" and r.printed == "refuse UNKNOWN_WORD: section_name"


def test_the_same_word_without_the_underscore_is_read() -> None:
    assert tolk.printed(tolk.read("Pip is a sectionname.")) == "tell   _sectionname_n_unknown(pip)"

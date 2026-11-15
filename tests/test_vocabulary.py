"""tolk.read takes a vocabulary: words the caller knows the class of (a database schema's names), given to the parser as tagged input."""

import tolk


def test_two_invented_words_are_read_with_the_classes_given() -> None:
    x = tolk.read("Which glorbs does Kim flibber?", vocabulary={"glorb": "n", "flibber": "v"})
    assert tolk.printed(x) == "ask X  _glorb_n_unknown(X), _flibber_v_unknown(E, kim, X)"


def test_the_classes_given_reach_the_parser_as_tags() -> None:
    from tolk import erg
    seen = []
    real = erg.parse
    erg.parse = lambda text, tags=None, limit=erg.READINGS: (seen.append(tags), real(text, tags, limit))[1]
    try:
        tolk.read("Which glorbs does Kim flibber?", vocabulary={"glorb": "n", "flibber": "v"})
    finally:
        erg.parse = real
    assert seen[0] == {"glorbs": ("NNS",), "flibber": ("VB", "VBP")}


def test_a_count_over_a_given_noun() -> None:
    x = tolk.read("How many glorbs does Kim flibber?", vocabulary={"glorb": "n", "flibber": "v"})
    assert isinstance(x, tolk.Ask) and x.count is not None


def test_a_word_of_a_class_the_store_cannot_hold_is_refused_for_the_caller() -> None:
    import pytest
    with pytest.raises(ValueError):
        tolk.read("Kim flibbers.", vocabulary={"flibber": "x"})

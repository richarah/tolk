"""Mismatches from VERIFY.md (round 1), each a failing test before its fix."""

import pytest

from tolk.mind import Mind


@pytest.mark.parametrize("text", ["Every dog that does not bark is quiet.", "Every cat that does not purr is grumpy."])
def test_10_a_relative_clause_with_not_is_never_stored_as_a_rule_with_a_conjunction_in_its_body(text: str) -> None:
    r = Mind().hear(text)
    assert "_not_c" not in r.printed, r.printed


@pytest.mark.parametrize("text, rule", [
    ("If Luna paints, Bruno is happy.", "rule   _happy_a_with(E!, bruno) :- _paint_v_1(E1, luna)"),
    ("Bruno is happy if Luna paints.", "rule   _happy_a_with(E!, bruno) :- _paint_v_1(E1, luna)"),
])
def test_6_if_read_as_a_preposition_does_not_end_the_search_for_the_reading_where_it_is_a_conjunction(text: str, rule: str) -> None:
    r = Mind().hear(text)
    assert r.printed == rule and r.outcome == "rule stored"

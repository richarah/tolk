"""Mismatches from VERIFY.md (round 1), each a failing test before its fix."""

import pytest

from tolk.mind import Mind


@pytest.mark.parametrize("text", ["Every dog that does not bark is quiet.", "Every cat that does not purr is grumpy."])
def test_10_a_relative_clause_with_not_is_never_stored_as_a_rule_with_a_conjunction_in_its_body(text: str) -> None:
    r = Mind().hear(text)
    assert "_not_c" not in r.printed, r.printed

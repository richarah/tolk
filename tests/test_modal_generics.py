"""A modal over a generic (a bare plural, or every) is refused as a modal in a rule, with the label the docs give. A modal over a named
subject or an indefinite is stored as before. Written first: the verification round found "Birds can fly." stored as one unnamed bird,
and "Every bird can fly." refused with the quantifier label."""

import pytest

from tolk.mind import Mind


@pytest.mark.parametrize("text", ["Birds can fly.", "Every bird can fly.", "All birds must sleep.", "Dogs should bark."])
def test_a_modal_over_a_generic_is_refused_as_a_modal_in_a_rule(text: str) -> None:
    r = Mind().tell(text)
    assert r.outcome == "refused" and r.printed.startswith("refuse UNSUPPORTED_PREDICATE"), r.printed


def test_a_modal_over_a_named_thing_is_still_stored() -> None:
    assert Mind().tell("Tweety can fly.").outcome.startswith("stored")


def test_a_modal_over_an_indefinite_is_still_stored() -> None:
    m = Mind()
    assert m.tell("A bird can fly.").outcome.startswith("stored")
    assert m.ask("Can a bird fly?").answer.value in ("Yes", "Unknown")

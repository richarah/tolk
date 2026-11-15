"""Item 5 (housekeeping): describing a kind. "What is a fish?", "What is fish?" and "What are birds?" are DescribeKind(predicate)."""

import pytest

from tolk import lf
from tolk.mind import Mind


def robin_world() -> Mind:
    m = Mind()
    for s in ("Every robin is a bird.", "Tweety is a robin.", "Kim does not like fish."):
        assert m.tell(s).outcome.startswith(("stored", "rule stored")), s
    return m


@pytest.mark.parametrize("text, printed", [
    ("What is a fish?", "describe kind _fish_n_1"), ("What is fish?", "describe kind _fish_n_1"),
    ("What are birds?", "describe kind _bird_n_1"), ("What are fish?", "describe kind _fish_n_1"),
    ("What is love?", "describe kind _love_n_of-for"),
])
def test_the_three_forms_give_the_new_logical_form(text: str, printed: str) -> None:
    r = Mind().hear(text)
    assert r.printed == printed


def test_who_is_a_bird_still_asks_for_the_birds_and_a_named_thing_is_still_described() -> None:
    assert Mind().hear("Who is a bird?").printed == "ask X  _bird_n_1(X)"
    assert Mind().hear("What is Tweety?").printed == "describe tweety"


def test_what_is_a_robin_names_the_rule_and_tweety() -> None:
    out = robin_world().ask("What is a robin?").outcome
    assert out == 'Rules:\n  "Every robin is a bird."\nKnown: 1: Tweety'


def test_what_is_fish_names_kims_rule() -> None:
    assert robin_world().ask("What is fish?").outcome == 'Rules:\n  "Kim does not like fish."'


def test_what_is_a_bird_has_the_rule_and_the_things_derived() -> None:
    assert robin_world().ask("What is a bird?").outcome == 'Rules:\n  "Every robin is a bird."\nKnown: 1: Tweety'


def test_a_default_is_marked() -> None:
    m = Mind()
    m.tell("Birds fly.")
    assert m.ask("What are birds?").outcome == 'Rules:\n  "Birds fly."  (default)'


def test_a_word_with_nothing_stored_is_unknown() -> None:
    assert robin_world().ask("What is a zorp?").outcome == "Unknown"


def test_love_as_a_noun_is_described_from_the_verb_with_the_widening_shown() -> None:
    m = Mind()
    m.tell("I love Veronika.")
    out = m.ask("What is love?").outcome
    assert out == '(widened: love (noun) matched as love (verb))\nKnown: 1: love(you, veronika)  (told: "I love Veronika.")'


def test_the_widening_is_for_the_description_only() -> None:
    m = Mind()
    m.tell("I love Veronika.")
    assert m.ask("Is Veronika a love?").outcome == "Unknown"
    m.tell("Every love is a feeling.")  # a rule about the noun: it does not fire on the verb's facts
    assert m.db.execute("SELECT COUNT(*) FROM fact").fetchone() == (1,)


def test_a_kind_with_a_fact_about_the_kind_itself() -> None:
    m = Mind()
    m.tell("Every robin is a bird.")
    m.tell("Robin is rare.")
    out = m.ask("What is a robin?").outcome
    assert out.startswith('Rules:\n  "Every robin is a bird."') and "Facts about it:" in out

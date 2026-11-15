"""Ten own-word cases for describing a kind. The expected texts were written from the store's contents before the first run."""

from tolk.mind import Mind


def world(*told: str) -> Mind:
    m = Mind()
    for s in told:
        m.tell(s)
    return m


def test_1_a_kind_of_invented_words_names_its_rule_and_its_thing() -> None:
    m = world("Every zorp is a wug.", "Pip is a zorp.")
    assert m.ask("What is a zorp?").outcome == 'Rules:\n  "Every zorp is a wug."\nKnown: 1: Pip'


def test_2_the_other_side_of_the_rule_has_the_derived_thing() -> None:
    m = world("Every zorp is a wug.", "Pip is a zorp.")
    assert m.ask("What are wugs?").outcome == 'Rules:\n  "Every zorp is a wug."\nKnown: 1: Pip'


def test_3_twelve_things_are_counted_and_ten_are_listed() -> None:
    names = ["Ada", "Bo", "Cy", "Di", "Ed", "Flo", "Gus", "Hal", "Ian", "Jo", "Lou"]
    m = world("Every zorp is a wug.", "Pip is a zorp.", *[f"{n} is a zorp." for n in names])
    assert m.ask("What is a zorp?").outcome == 'Rules:\n  "Every zorp is a wug."\nKnown: 12: ' + ", ".join(sorted(names + ["Pip"])[:10])


def test_4_a_word_with_nothing_stored_is_unknown() -> None:
    assert world("Pip is a zorp.").ask("What is a quux?").outcome == "Unknown"


def test_5_an_invented_verb_asked_as_a_noun_is_widened_and_the_facts_listed() -> None:
    out = world("Pip flibbers.").ask("What is a flibber?").outcome
    assert out == '(widened: flibber (noun) matched as flibber (verb))\nKnown: 1: flibber(pip)  (told: "Pip flibbers.")'


def test_6_an_invented_adjective_asked_as_a_noun_is_widened() -> None:
    out = world("Pip is mimsy.").ask("What is a mimsy?").outcome
    assert out == '(widened: mimsy (noun) matched as mimsy (adjective))\nKnown: 1: mimsy(pip)  (told: "Pip is mimsy.")'


def test_7_a_default_is_marked_as_one() -> None:
    assert world("Dogs bark.").ask("What are dogs?").outcome == 'Rules:\n  "Dogs bark."  (default)'


def test_8_two_rules_are_listed_in_the_order_they_were_told() -> None:
    assert world("Every dog is an animal.", "Dogs bark.").ask("What is a dog?").outcome == 'Rules:\n  "Every dog is an animal."\n  "Dogs bark."  (default)'


def test_9_a_negative_rule_names_its_sentence() -> None:
    assert world("No cat barks.").ask("What is a cat?").outcome == 'Rules:\n  "No cat barks."'


def test_10_a_forgotten_rule_is_no_longer_described() -> None:
    m = world("Every dog is an animal.")
    assert m.ask("What is a dog?").outcome.startswith("Rules:")
    m.hear("Forget that every dog is an animal.")
    assert m.ask("What is a dog?").outcome == "Unknown"

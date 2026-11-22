"""Item 7: the wording setting. "template" (default) is the stiff wording; "generated" words each fact through the grammar and falls back
to the template for a fact it cannot word."""

import pytest

from tolk.mind import Mind

TOLD = ["Tweety is a bird.", "Every bird flies.", "Rio does not sing.", "Kim likes Sandy."]


def mind(wording: str) -> Mind:
    m = Mind(wording=wording)
    for s in TOLD:
        m.tell(s)
    return m


def test_the_default_is_generated_and_is_kept_in_meta() -> None:
    # Changed in the proofs item: generated wording is the default (DECISIONS.md, proofs). The template stays as the fallback.
    m = Mind()
    assert m.wording == "generated"
    assert m.db.execute("SELECT value FROM meta WHERE key = 'wording'").fetchone() == ("generated",)


def test_an_unknown_wording_is_refused() -> None:
    with pytest.raises(ValueError):
        Mind(wording="poetic")


def test_template_proofs_are_the_stiff_ones() -> None:
    assert mind("template").ask("Does Kim like Sandy?").outcome == 'Yes\nlike(kim, sandy)  (told: "Kim likes Sandy.")'


def test_generated_proofs_use_the_grammars_sentence_for_each_fact_it_can_word() -> None:
    m = mind("generated")
    assert m.ask("Does Kim like Sandy?").outcome == 'Yes\nKim likes Sandy.  (told: "Kim likes Sandy.")'
    assert m.ask("Does Rio sing?").outcome == 'No\nRio doesn\'t sing.  (told: "Rio does not sing.")'


def test_each_fact_is_worded_on_its_own_and_one_the_grammar_cannot_word_keeps_the_template() -> None:
    m = mind("generated")
    assert m.ask("Does Tweety fly?").outcome.splitlines()[1:] == ["Tweety flies.  (by rule 1)", '  Tweety is a bird.  (told: "Tweety is a bird.")']
    m.tell("Kim owns a cat.")
    out = m.ask("Does Kim own a cat?").outcome
    assert "own(kim, a1)  (told" in out and "a1 is a cat" in out  # things the grammar has no name for stay in the template


def test_the_setting_can_change_during_a_session() -> None:
    m = mind("template")
    m.set_wording("generated")
    assert m.ask("Does Kim like Sandy?").outcome.splitlines()[1].startswith("Kim likes Sandy.")

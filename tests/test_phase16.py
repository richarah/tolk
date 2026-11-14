"""Phase 16: words the grammar does not know. What the fixtures show: an unknown word becomes _surface/TAG_u_unknown with a rough
part of speech from the grammar's tagger, so a noun or adjective can be used; a verb in a question, or two unknown words, give no usable reading."""

import pytest

from tolk.ask import UNKNOWN, YES
from tolk.mind import Mind


@pytest.fixture()
def mind() -> Mind:
    return Mind()


def test_the_four_sentences(mind: Mind) -> None:
    assert mind.tell("Tweety is a blorp.").printed == "tell   _blorp_n_unknown(tweety)"
    r = mind.hear("Every blorp flibbers.")
    assert r.outcome == "refused"  # no reading at all: two words are unknown to the grammar
    assert mind.tell("Tweety is glorpy.").printed.startswith("tell   _glorpy_a_unknown(e1, tweety)")
    r = mind.hear("Does Tweety flibber?")
    assert r.outcome == "refused" and r.printed == "refuse UNKNOWN_WORD: flibber"
    # Nothing that was stored is wrong, and nothing was invented.
    assert {p for (p,) in mind.db.execute("SELECT DISTINCT pred FROM fact")} == {"_blorp_n_unknown", "_glorpy_a_unknown"}


def test_an_unknown_noun_and_adjective_behave_like_known_ones(mind: Mind) -> None:
    mind.tell("Pip is a zorp.")
    mind.tell("Ada is floopy.")
    mind.tell("Every zorp is floopy.")
    assert mind.ask("Is Pip a zorp?").answer.value == YES
    assert mind.ask("Who is a zorp?").outcome.splitlines()[0] == "Pip"
    assert mind.ask("Is Ada a zorp?").answer.value == UNKNOWN


def test_the_adjective_a_question_reads_as_a_noun_is_matched_and_the_widening_is_shown(mind: Mind) -> None:
    mind.tell("Ada is floopy.")
    r = mind.ask("Is Ada floopy?")
    assert r.answer.value == YES and "_floopy_n_unknown matched as _floopy_a_unknown" in r.outcome


def test_a_derived_adjective_answers_a_question(mind: Mind) -> None:
    mind.tell("Pip is a zorp.")
    mind.tell("Every zorp is floopy.")
    assert mind.ask("Is Pip floopy?").answer.value == YES


def test_an_unknown_verb_in_a_statement_is_stored_and_found_by_who(mind: Mind) -> None:
    assert mind.tell("Pip glorbs.").printed == "tell   _glorb_v_unknown(e1, pip)"
    assert mind.ask("Who glorbs?").outcome.splitlines()[0] == "Pip"


def test_an_unknown_verb_in_a_yes_no_question_is_refused_by_name(mind: Mind) -> None:
    mind.tell("Pip glorbs.")
    for q in ("Does Pip glorb?", "Does Ada glorb?"):
        r = mind.hear(q)
        assert r.outcome == "refused" and r.printed == "refuse UNKNOWN_WORD: glorb"


def test_an_unknown_word_is_not_a_known_word(mind: Mind) -> None:
    mind.tell("Pip is a zorp.")
    assert mind.ask("Is Pip a bird?").answer.value == UNKNOWN


def test_an_unknown_verb_is_never_widened_to_another_part_of_speech() -> None:
    from tolk import ask, lf
    from tolk.lf import Atom, Const, Var
    m = Mind()
    m.tell("Pip is a glorb.")
    q = lf.Ask((Atom("_glorb_v_unknown", (Var("e"), Const("pip"))),), ())
    assert ask.answer(m.db, q).value == UNKNOWN

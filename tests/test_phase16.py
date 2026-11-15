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
    # Audit 2B: the verb question is read with the verb class offered, so it is understood; nothing says Tweety flibbers.
    assert mind.ask("Does Tweety flibber?").answer.value == UNKNOWN
    # Nothing that was stored is wrong, and nothing was invented.
    assert {p for (p,) in mind.db.execute("SELECT DISTINCT pred FROM fact")} == {"_blorp_n_unknown", "_glorpy_a_unknown"}


def test_an_unknown_noun_and_adjective_behave_like_known_ones(mind: Mind) -> None:
    mind.tell("Pip is a zorp.")
    mind.tell("Ada is floopy.")
    mind.tell("Every zorp is floopy.")
    assert mind.ask("Is Pip a zorp?").answer.value == YES
    assert mind.ask("Who is a zorp?").outcome.splitlines()[0] == "Pip"
    assert mind.ask("Is Ada a zorp?").answer.value == UNKNOWN


def test_the_adjective_is_asked_as_an_adjective_because_its_class_is_remembered(mind: Mind) -> None:
    # Before audit 2B the tagger read it as a noun in the question and the match was widened; now the first use's class is given to the parser.
    mind.tell("Ada is floopy.")
    r = mind.ask("Is Ada floopy?")
    assert r.answer.value == YES and "widened" not in r.outcome


def test_a_derived_adjective_answers_a_question(mind: Mind) -> None:
    mind.tell("Pip is a zorp.")
    mind.tell("Every zorp is floopy.")
    assert mind.ask("Is Pip floopy?").answer.value == YES


def test_an_unknown_verb_in_a_statement_is_stored_and_found_by_who(mind: Mind) -> None:
    assert mind.tell("Pip glorbs.").printed == "tell   _glorb_v_unknown(e1, pip)"
    assert mind.ask("Who glorbs?").outcome.splitlines()[0] == "Pip"


def test_an_unknown_verb_in_a_yes_no_question_is_answered_from_its_remembered_class(mind: Mind) -> None:
    mind.tell("Pip glorbs.")
    assert mind.ask("Does Pip glorb?").answer.value == YES
    assert mind.ask("Does Ada glorb?").answer.value == UNKNOWN


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

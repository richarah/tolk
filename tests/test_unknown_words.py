"""Unknown words, second pass (audit Part 2B): the class a word was first used as is remembered, and given to the parser as a
part-of-speech tag (ACE's -y input) when a later sentence uses the word. The acceptance sentences are the task's."""

from tolk.ask import UNKNOWN, YES
from tolk.mind import Mind


def test_after_a_noun_and_a_verb_are_told_the_questions_are_yes() -> None:
    m = Mind()
    assert m.tell("Tweety is a blorp.").outcome.startswith("stored")
    assert m.tell("Tweety flibbers.").outcome.startswith("stored")
    assert m.ask("Does Tweety flibber?").answer.value == YES
    assert m.ask("Is Tweety a blorp?").answer.value == YES


def test_the_class_is_remembered_from_the_first_accepted_use_of_each_class() -> None:
    m = Mind()
    for text in ("Pip is a zorp.", "Ada is floopy.", "Pip glorbs.", "Pip is a glorb.", "Ada is a zorp."):
        m.tell(text)
    rows = m.db.execute("SELECT w.lemma, w.pos, s.text FROM word w JOIN sentence s ON s.id = w.sentence ORDER BY w.lemma, w.pos").fetchall()
    assert rows == [("floopy", "a", "Ada is floopy."), ("glorb", "n", "Pip is a glorb."), ("glorb", "v", "Pip glorbs."), ("zorp", "n", "Pip is a zorp.")]


def test_a_word_used_as_two_classes_is_offered_as_both_and_the_syntax_picks() -> None:
    m = Mind()
    m.tell("Pip is a glorb.")
    m.tell("Pip glorbs.")
    assert m.ask("Is Pip a glorb?").answer.value == YES
    assert m.ask("Does Pip glorb?").answer.value == YES


def test_a_remembered_class_is_given_to_the_parser_not_guessed_again() -> None:
    # The parser's own tagging reads "floopy" in a question as a noun; the remembered class makes it the adjective that was told.
    m = Mind()
    m.tell("Ada is floopy.")
    r = m.ask("Is Ada floopy?")
    assert r.printed == "ask    _floopy_a_unknown(E, ada)" and r.answer.value == YES


def test_a_past_tense_is_refused_not_stored_as_a_present_verb() -> None:
    m = Mind()
    r = m.hear("Tweety flibbered.")
    assert r.outcome == "refused" and r.printed == "refuse UNKNOWN_WORD: flibbered"
    assert m.db.execute("SELECT COUNT(*) FROM fact").fetchone()[0] == 0


def test_a_sentence_with_two_unknown_words_the_parser_cannot_read_is_read_with_every_class_offered() -> None:
    # The grammar gives no reading, so every small-letter word is offered the classes it could be (finish, item 3).
    r = Mind().hear("Every blorp flibbers.")
    assert r.outcome == "rule stored" and r.printed == "rule   _flibber_v_unknown(E!, X) :- _blorp_n_unknown(X)"

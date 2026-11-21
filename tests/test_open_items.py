"""The open items of the release (STATUS.md), each with a failing test written first."""

import pytest

from tolk import lf
from tolk.ask import NO, UNKNOWN, YES
from tolk.mind import Mind


# 4. An or between two clauses, one of which is a conjunction: the alternative about one side keeps only that side's atoms.
def test_a_conjunction_side_of_an_or_does_not_carry_the_other_side() -> None:
    m = Mind()
    m.tell("Sam is happy.")
    assert m.ask("Are Kim and Lee happy or is Sam happy?").answer.value == YES


def test_the_conjunction_side_is_still_needed_for_its_own_yes() -> None:
    m = Mind()
    m.tell("Kim is happy.")
    assert m.ask("Are Kim and Lee happy or is Sam happy?").answer.value == UNKNOWN
    m.tell("Lee is happy.")
    assert m.ask("Are Kim and Lee happy or is Sam happy?").answer.value == YES


def test_the_or_alternatives_name_their_own_sides() -> None:
    import tolk
    q = tolk.read("Are Kim and Lee happy or is Sam happy?")
    assert isinstance(q, lf.Ask) and len(q.alternatives) == 2
    names = [{t.id for a in alt for t in a.args if isinstance(t, lf.Const)} for alt in q.alternatives]
    assert {"kim", "lee"} <= names[0] and "sam" not in names[0]
    assert "sam" in names[1] and "lee" not in names[1]


# 5. A past tense in an or question: each side's clause may be past, as it may be in a sentence with and or or.
@pytest.mark.parametrize("told, question, answer", [
    (["Lee sang."], "Did Kim sing or did Lee sing?", YES),
    (["Kim sang."], "Did Kim sing or did Lee sing?", YES),
    (["Kim is sad."], "Was Kim happy or was Lee sad?", UNKNOWN),
    (["Lee was sad."], "Was Kim happy or was Lee sad?", YES),
])
def test_past_tense_on_each_side_of_an_or_question(told: list[str], question: str, answer: str) -> None:
    m = Mind()
    for s in told:
        m.tell(s)
    assert m.ask(question).answer.value == answer


def test_past_tense_on_each_clause_of_an_and_statement_is_stored() -> None:
    m = Mind()
    assert m.tell("Kim sang and Lee danced.").outcome == "stored, 4 new fact(s)"
    assert m.ask("Did Lee dance?").answer.value == YES


def test_a_past_tense_clause_joined_by_or_in_a_statement_is_still_refused() -> None:
    assert Mind().tell("Kim sang or Lee danced.").outcome == "refused"


# 1. "Tweety is a blips." has no reading at all. The refusal names the word whose replacement makes the sentence parse.
def test_a_sentence_with_no_reading_is_refused_for_the_word_that_stops_it() -> None:
    r = Mind().tell("Tweety is a blips.")
    assert r.outcome == "refused"
    assert r.printed == "refuse UNKNOWN_WORD: blips"


def test_blips_are_things_is_a_default_rule_about_the_word() -> None:
    m = Mind()
    assert m.tell("Blips are things.").outcome == "rule stored"
    assert m.tell("Tweety is a blip.").outcome.startswith("stored")
    assert m.ask("Is Tweety a thing?").answer.value == YES


# 2. "Ola owns more than two cellos." is refused for its word, because a word the grammar does not know is named first
# (the rule for dogs and cats, which are known words, is more_comp, the declined comparison).
def test_more_than_with_an_unknown_plural_is_refused_for_the_word() -> None:
    assert Mind().tell("Ola owns more than two cellos.").printed == "refuse UNKNOWN_WORD: cellos"


def test_more_than_with_a_known_noun_is_refused_as_a_comparison() -> None:
    assert Mind().tell("Ola owns more than two dogs.").printed == "refuse UNSUPPORTED_PREDICATE: more_comp"


# 3. "Quorl is a thing." is a capitalised word at the start: a name. That is the decision recorded in DECISIONS.md.
def test_a_capitalised_unknown_word_is_a_name_and_a_thing() -> None:
    m = Mind()
    assert m.tell("Quorl is a thing.").outcome.startswith("stored")
    assert m.ask("Is Quorl a thing?").answer.value == YES


def test_did_kim_sing_or_lee_dance_on_an_empty_store_is_a_question() -> None:
    # Was refused NO_EVENT_READING on a store with no facts; the or-split and the tense rule fix it, and the store does not steer it.
    assert Mind().ask("Did Kim sing or Lee dance?").printed == "ask    _sing_v_1(E, kim) | _dance_v_1(E1, lee)  [E past]  [E1 past]"

"""Reading choice, criterion by criterion (DECISIONS.md, "reading choice"). Each criterion has a sentence where it decides
and a sentence where it must not change the outcome. Readings come from recorded fixtures."""

from helpers import readings_of
from tolk import choice, compile as comp, sem


def readings(text: str) -> list[sem.Reading]:
    return readings_of(text)


def chosen(text: str, store: set | None = None) -> int:
    return comp.choose(readings(text), store or set())[0] + 1


# 1. Refusals
def test_a_final_refusal_decides_nobody_is_not_read_as_a_name() -> None:
    k, x = comp.choose(readings("Nobody flies."), set())
    assert x.code == "UNSUPPORTED_PREDICATE" and k == 1


def test_a_reading_refusal_changes_nothing_the_name_reading_of_fish_is_skipped() -> None:
    assert chosen("Fish do not fly.") == 2


# 2. Store overlap
def test_overlap_decides_a_stored_verb_sense_wins() -> None:
    assert chosen("Sam works in Paris.") == 1
    assert chosen("Sam works in Paris.", {("_work_v_in", 3)}) == 2


def test_overlap_changes_nothing_when_the_store_shares_no_predicate() -> None:
    assert chosen("Sam works in Paris.", {("_sing_v_1", 2)}) == 1


# 3. Swallowed words
def test_swallowed_words_decide_the_verb_reading_of_fish_loses() -> None:
    assert chosen("Kim does not like fish.") == 2


def test_swallowed_words_change_nothing_an_unspanned_auxiliary_is_free() -> None:
    assert chosen("Kim does not like Sandy.") == 1


# 4. Parser order
def test_parser_order_decides_between_two_equal_readings() -> None:
    assert chosen("Kim lives in Oslo.") == 1


def test_parser_order_is_overridden_by_overlap() -> None:
    assert chosen("Kim lives in Oslo.", {("_in_p_state", 2)}) == 2


def test_a_fallback_parse_is_a_reading_refusal_and_is_skipped() -> None:
    # Reading 1 of this sentence leaves a word unanalysed; reading 2 is the sentence.
    k, x = comp.choose(readings("Rio hums if Rio is a sparrow."), set())
    assert k == 1 and not hasattr(x, "code")


# Part 2 of the audit changed the order to: generic entries, store overlap, swallowed words, parser order (compile only breaks a tie).
def test_a_generic_entry_for_a_word_the_grammar_knows_loses_nobody_is_not_a_name() -> None:
    assert choice.preferred(readings("Nobody flies."), set()) == [1]


def test_generic_entries_change_nothing_when_every_reading_uses_one() -> None:
    # Tweety is no word of the grammar, so no reading is worse for naming it.
    assert chosen("Tweety flies.") == 3


def test_overlap_comes_before_swallowed_words_a_stored_particle_verb_wins() -> None:
    # The verb sense that takes "in" as a particle leaves the word "in" without a predication of its own; the store decides first.
    assert choice.measures(readings("Sam works in Paris."), 1, {("_work_v_in", 3)})[2] == 1
    assert chosen("Sam works in Paris.", {("_work_v_in", 3)}) == 2


def test_only_the_readings_tied_on_every_measure_are_compiled() -> None:
    assert choice.preferred(readings("Kim does not like fish."), set()) == [1, 2, 3, 4]
    assert choice.preferred(readings("Does Kim know that Rio flies?"), {("_know_v_1", 3), ("_fly_v_1", 2)}) == [1, 2]

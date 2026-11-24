"""Negated events: a negated statement keeps its tense, modal and progressive. The negative fact has an event of its own, which carries
them as a positive fact's event does, so "Kim does not sing.", "Kim did not sing." and "Kim will not sing." are three facts. A negative
fact contradicts only a positive one of the same tense, modal and progressive, and a question about another one is Unknown."""

import pytest

from tolk import say
from tolk.ask import CONFLICT, NO, UNKNOWN, YES
from tolk.mind import Mind


def answers(told: list[str], questions: list[str], **kw) -> list[str]:
    m = Mind(**kw)
    for s in told:
        assert m.tell(s).outcome.startswith(("stored", "rule stored")), s
    return [m.ask(q).answer.value for q in questions]


def test_a_negated_statement_is_stored_with_its_tense() -> None:
    m = Mind()
    assert m.tell("Kim did not sing.").printed == "tell   not _sing_v_1(e1, kim)\ntell   tense(e1, past)"
    assert m.tell("Kim will not sing.").printed == "tell   not _sing_v_1(e1, kim)\ntell   tense(e1, fut)"
    assert m.tell("Kim does not sing.").printed == "tell   not _sing_v_1(e1, kim)"
    # Three facts, one per tense: none is folded into another.
    assert m.db.execute("SELECT COUNT(*) FROM fact WHERE pred = '_sing_v_1' AND positive = 0").fetchone()[0] == 3


def test_negated_progressives_and_modals_are_stored_with_their_mark() -> None:
    m = Mind()
    assert m.tell("Kim is not singing.").printed == "tell   not _sing_v_1(e1, kim)\ntell   modal(e1, prog)"
    assert m.tell("Lee cannot sing.").printed == "tell   not _sing_v_1(e1, lee)\ntell   modal(e1, can)"
    assert m.tell("Ada must not sing.").printed == "tell   not _sing_v_1(e1, ada)\ntell   modal(e1, must)"
    assert m.tell("Bo was not singing.").printed == "tell   not _sing_v_1(e1, bo)\ntell   tense(e1, past)\ntell   modal(e1, prog)"


@pytest.mark.parametrize("first, second", [
    ("Kim does not sing.", "Kim sang."),
    ("Kim sang.", "Kim does not sing."),
    ("Kim did not sing.", "Kim sings."),
    ("Kim will not sing.", "Kim sang."),
    ("Kim did not sing.", "Kim will sing."),
    ("Kim cannot sing.", "Kim sings."),
    ("Kim cannot sing.", "Kim must sing."),
    ("Kim is not singing.", "Kim sings."),
    ("Kim does not sing.", "Kim is singing."),
    ("Kim was not singing.", "Kim is singing."),
    ("Kim was not singing.", "Kim sang."),
])
def test_statements_of_different_sorts_do_not_contradict(first: str, second: str) -> None:
    m = Mind()
    assert m.tell(first).outcome.startswith("stored")
    assert m.tell(second).outcome.startswith("stored"), second


@pytest.mark.parametrize("first, second", [
    ("Kim did not sing.", "Kim sang."),
    ("Kim sang.", "Kim did not sing."),
    ("Kim does not sing.", "Kim sings."),
    ("Kim will not sing.", "Kim will sing."),
    ("Kim is not singing.", "Kim is singing."),
    ("Kim was not singing.", "Kim was singing."),
    ("Kim cannot sing.", "Kim can sing."),
    ("Kim can sing.", "Kim cannot sing."),
    ("Kim must not sing.", "Kim must sing."),
    ("Kim could not sing.", "Kim could sing."),
    ("Ada did not like Bo.", "Ada liked Bo."),
    ("Ada was not happy.", "Ada was happy."),
])
def test_statements_of_the_same_sort_still_contradict(first: str, second: str) -> None:
    m = Mind()
    assert m.tell(first).outcome.startswith("stored")
    assert m.tell(second).outcome.startswith("refused, contradicts"), second


@pytest.mark.parametrize("told, question, answer", [
    ("Kim did not sing.", "Did Kim sing?", NO),
    ("Kim did not sing.", "Did Kim not sing?", YES),
    ("Kim did not sing.", "Does Kim sing?", UNKNOWN),
    ("Kim did not sing.", "Will Kim sing?", UNKNOWN),
    ("Kim did not sing.", "Does Kim not sing?", UNKNOWN),
    ("Kim does not sing.", "Does Kim sing?", NO),
    ("Kim does not sing.", "Does Kim not sing?", YES),
    ("Kim does not sing.", "Did Kim sing?", UNKNOWN),
    ("Kim does not sing.", "Will Kim sing?", UNKNOWN),
    ("Kim does not sing.", "Can Kim sing?", UNKNOWN),
    ("Kim does not sing.", "Is Kim singing?", UNKNOWN),
    ("Kim will not sing.", "Will Kim sing?", NO),
    ("Kim will not sing.", "Will Kim not sing?", YES),
    ("Kim will not sing.", "Does Kim sing?", UNKNOWN),
    ("Kim will not sing.", "Did Kim sing?", UNKNOWN),
    ("Kim is not singing.", "Is Kim singing?", NO),
    ("Kim is not singing.", "Is Kim not singing?", YES),
    ("Kim is not singing.", "Does Kim sing?", UNKNOWN),
    ("Kim is not singing.", "Was Kim singing?", UNKNOWN),
    ("Kim was not singing.", "Was Kim singing?", NO),
    ("Kim was not singing.", "Is Kim singing?", UNKNOWN),
    ("Kim was not singing.", "Did Kim sing?", UNKNOWN),
    ("Kim cannot sing.", "Can Kim sing?", NO),
    ("Kim cannot sing.", "Can Kim not sing?", YES),
    ("Kim cannot sing.", "Does Kim sing?", UNKNOWN),
    ("Kim cannot sing.", "Must Kim sing?", UNKNOWN),
    ("Kim must not sing.", "Must Kim sing?", NO),
    ("Kim must not sing.", "Can Kim sing?", UNKNOWN),
    ("Kim could not sing.", "Could Kim sing?", NO),
    ("Ada did not like Bo.", "Did Ada like Bo?", NO),
    ("Ada did not like Bo.", "Does Ada like Bo?", UNKNOWN),
    ("Ada was not happy.", "Was Ada happy?", NO),
    ("Ada was not happy.", "Is Ada happy?", UNKNOWN),
])
def test_a_question_is_answered_only_by_a_negation_of_its_own_sort(told: str, question: str, answer: str) -> None:
    assert answers([told], [question]) == [answer]


def test_a_negation_and_a_positive_of_other_sorts_answer_their_own_questions() -> None:
    # The issue's example: before, "Kim does not sing." and "Kim sang." contradicted each other.
    got = answers(["Kim does not sing.", "Kim sang.", "Kim cannot dance.", "Kim dances."],
                  ["Does Kim sing?", "Did Kim sing?", "Can Kim dance?", "Does Kim dance?"])
    assert got == [NO, YES, NO, YES]


def test_who_questions_see_the_tense_of_a_negation() -> None:
    m = Mind()
    for s in ["Kim did not sing.", "Lee sang.", "Ada does not sing."]:
        m.tell(s)
    assert m.ask("Who sang?").outcome.startswith("Lee")


def test_a_negated_rule_conclusion_keeps_its_tense() -> None:
    m = Mind()
    assert m.tell("Kim did not like fish.").printed == "rule   not _like_v_1(E!, kim, X), tense(E, past) :- _fish_n_1(X)"
    m.tell("Nemo is a fish.")
    assert m.ask("Did Kim like Nemo?").answer.value == NO
    assert m.ask("Did Kim not like Nemo?").answer.value == YES
    assert m.ask("Does Kim like Nemo?").answer.value == UNKNOWN
    assert m.tell("Kim likes Nemo.").outcome.startswith("stored")
    assert m.tell("Kim liked Nemo.").outcome.startswith("refused, contradicts")


def test_a_present_negated_rule_is_still_about_the_present() -> None:
    m = Mind()
    assert m.tell("Oskar does not like fish.").printed == "rule   not _like_v_1(_, oskar, X) :- _fish_n_1(X)"
    m.tell("Nemo is a fish.")
    r = m.ask("Does Oskar like Nemo?")
    assert r.answer.value == NO
    assert "not like(oskar, nemo)  (by rule 1)" in r.outcome and "Nemo is a fish.  (told:" in r.outcome
    assert m.ask("Did Oskar like Nemo?").answer.value == UNKNOWN
    assert m.tell("Oskar liked Nemo.").outcome.startswith("stored")
    assert m.tell("Oskar likes Nemo.").outcome.startswith("refused, contradicts")


def test_a_no_rule_does_not_deny_a_past_event() -> None:
    m = Mind()
    for s in ["No penguin flies.", "Pingu is a penguin."]:
        m.tell(s)
    assert m.ask("Does Pingu fly?").answer.value == NO
    assert m.ask("Did Pingu fly?").answer.value == UNKNOWN
    assert m.tell("Pingu flew.").outcome.startswith("stored")
    assert m.ask("Did Pingu fly?").answer.value == YES
    assert m.ask("Does Pingu fly?").answer.value == NO


def test_a_default_is_defeated_only_by_a_negation_of_its_own_sort() -> None:
    m = Mind()
    for s in ["Birds fly.", "Tweety is a bird.", "Tweety did not fly."]:
        m.tell(s)
    assert m.ask("Does Tweety fly?").answer.value == YES
    assert m.ask("Did Tweety fly?").answer.value == NO
    m.tell("Tweety does not fly.")
    assert m.ask("Does Tweety fly?").answer.value == NO


def test_a_derived_clash_of_the_same_sort_is_a_conflict() -> None:
    m = Mind()
    for s in ["Kim did not sing.", "Every singer sang.", "Kim is a singer."]:
        m.tell(s)
    assert m.ask("Did Kim sing?").answer.value == CONFLICT
    m2 = Mind()
    for s in ["Kim does not sing.", "Every singer sang.", "Kim is a singer."]:
        m2.tell(s)
    assert m2.ask("Did Kim sing?").answer.value == YES
    assert m2.ask("Does Kim sing?").answer.value == NO


def test_the_closed_world_keeps_the_tense_of_a_negated_question() -> None:
    assert answers(["Kim sang."], ["Does Kim not sing?", "Did Kim not sing?"], closed_world=True) == [YES, NO]


@pytest.mark.parametrize("told, question, wording", [
    ("Rio does not sing.", "Does Rio sing?", "Rio doesn't sing."),
    ("Rio did not sing.", "Did Rio sing?", "Rio didn't sing."),
    ("Rio will not sing.", "Will Rio sing?", "Rio won't sing."),
    ("Rio is not singing.", "Is Rio singing?", "Rio isn't singing."),
    ("Rio was not singing.", "Was Rio singing?", "Rio wasn't singing."),
    ("Rio cannot sing.", "Can Rio sing?", "Rio can't sing."),
    ("Ada did not like Bo.", "Did Ada like Bo?", "Ada didn't like Bo."),
    ("Ada was not happy.", "Was Ada happy?", "Ada wasn't happy."),
])
def test_a_negative_fact_is_worded_with_its_tense_and_modal(told: str, question: str, wording: str) -> None:
    m = Mind()
    m.tell(told)
    assert m.ask(question).outcome == f'No\n{wording}  (told: "{told}")'


@pytest.mark.parametrize("told, question, wording", [
    ("Rio does not sing.", "Does Rio sing?", "not sing(rio)"),
    ("Rio did not sing.", "Did Rio sing?", "not sing(rio) [past]"),
    ("Rio was not singing.", "Was Rio singing?", "not sing(rio) [past, prog]"),
    ("Rio cannot sing.", "Can Rio sing?", "not sing(rio) [can]"),
])
def test_the_template_shows_the_tense_and_modal_of_a_negative_fact(told: str, question: str, wording: str) -> None:
    m = Mind(wording="template")
    m.tell(told)
    assert m.ask(question).outcome == f'No\n{wording}  (told: "{told}")'


def test_a_repeat_is_caught_only_in_the_same_tense() -> None:
    m = Mind()
    m.tell("Kim did not sing.")
    assert m.tell("Kim did not sing.").outcome == 'already told: "Kim did not sing."'
    assert m.tell("Kim does not sing.").outcome.startswith("stored")


def test_forgetting_a_negation_forgets_only_its_tense() -> None:
    m = Mind()
    m.tell("Kim did not sing.")
    m.tell("Kim does not sing.")
    assert m.tell("forget that Kim did not sing.").outcome == 'forgot "Kim did not sing."'
    assert m.ask("Did Kim sing?").answer.value == UNKNOWN
    assert m.ask("Does Kim sing?").answer.value == NO


def test_the_negative_fact_has_an_event_entity() -> None:
    m = Mind()
    m.tell("Kim did not sing.")
    (event,) = m.db.execute("SELECT a0 FROM fact WHERE pred = '_sing_v_1' AND positive = 0").fetchone()
    assert m.db.execute("SELECT kind FROM entity WHERE id = ?", (event,)).fetchone() == ("event",)
    (fid,) = m.db.execute("SELECT id FROM fact WHERE pred = '_sing_v_1'").fetchone()
    assert say.fact_text(m.db, fid) == "not sing(kim) [past]"


def test_an_opposite_word_denies_its_base_in_the_same_tense() -> None:
    # un- makes a negative fact about the same event, so it keeps the event's tense.
    m = Mind()
    m.tell("Pip is glorby.")
    m.tell("Kim was unglorby.")
    assert m.ask("Was Kim glorby?").answer.value == NO
    assert m.ask("Is Kim glorby?").answer.value == UNKNOWN
    assert m.tell("Kim was glorby.").outcome.startswith("refused, contradicts")
    assert m.tell("Kim is glorby.").outcome.startswith("stored")


def test_a_negated_clause_in_a_claim_is_asked_as_told() -> None:
    # The told and the asked content both give the negated clause an event, so they compare.
    m = Mind()
    m.tell("Kim believes that Rio does not fly.")
    assert m.ask("Does Kim believe that Rio does not fly?").answer.value == YES
    assert m.ask("Does Kim believe that Rio flies?").answer.value == UNKNOWN


def test_a_negation_keeps_its_tense_when_the_store_is_reopened(tmp_path) -> None:
    path = str(tmp_path / "store.db")
    m = Mind(path)
    m.tell("Mia did not paint.")
    m.tell("Mia cannot paint.")
    m.tell("Mia is not painting.")
    del m
    m = Mind(path)
    assert [m.ask(q).answer.value for q in ("Did Mia paint?", "Does Mia paint?", "Can Mia paint?", "Is Mia painting?", "Will Mia paint?")] == [NO, UNKNOWN, NO, NO, UNKNOWN]
    assert m.tell("Mia painted.").outcome.startswith("refused, contradicts")
    assert m.tell("Mia paints.").outcome.startswith("stored")


def test_a_contracted_negation_and_a_negated_present_perfect_are_past_negations() -> None:
    assert answers(["John didn't eat."], ["Did John eat?", "Does John eat?"]) == [NO, UNKNOWN]
    assert answers(["Anna has not left."], ["Did Anna leave?", "Has Anna left?", "Does Anna leave?"]) == [NO, NO, UNKNOWN]
    m = Mind()
    m.tell("John didn't eat.")
    assert m.tell("John ate.").outcome.startswith("refused, contradicts")
    assert m.tell("John eats.").outcome.startswith("stored")


def test_a_proof_for_each_negated_kind_is_worded_in_its_own_kind() -> None:
    m = Mind()
    m.set_wording("generated")
    for told in ("Ann did not dance.", "Ann will not dance.", "Ann cannot dance.", "Ann is not dancing."):
        m.tell(told)
    lines = [m.ask(q).outcome.splitlines()[1] for q in ("Did Ann dance?", "Will Ann dance?", "Can Ann dance?", "Is Ann dancing?")]
    assert [x.split("  (")[0] for x in lines] == ["Ann didn't dance.", "Ann won't dance.", "Ann can't dance.", "Ann isn't dancing."]

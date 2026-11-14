"""Phase 14: numbers. The dialogue is SPEC2's; the rest use other words. Expectations were written before the code."""

import pytest

from tolk.ask import UNKNOWN, YES
from tolk.mind import Mind


@pytest.fixture()
def mind() -> Mind:
    return Mind()


def first(m: Mind, text: str) -> str:
    return m.hear(text).outcome.splitlines()[0]


def test_the_dialogue(mind: Mind) -> None:
    mind.tell("Kim owns two cats.")
    assert first(mind, "How many cats does Kim own?") == "2"
    assert first(mind, "Does Kim own two cats?") == "Yes"
    assert first(mind, "Does Kim own three cats?") == "Unknown"
    mind.tell("Kim owns a cat.")
    assert first(mind, "How many cats does Kim own?") == "3"


def test_each_thing_is_distinct_and_has_its_own_facts(mind: Mind) -> None:
    mind.tell("Bo admires two teachers.")
    assert mind.db.execute("SELECT COUNT(DISTINCT a2) FROM fact WHERE pred = '_admire_v_1'").fetchone()[0] == 2
    assert mind.db.execute("SELECT COUNT(*) FROM fact WHERE pred = '_teacher_n_of'").fetchone()[0] == 2


@pytest.mark.parametrize("told, question, answer", [
    (["Bo admires two teachers."], "How many teachers does Bo admire?", "2"),
    (["Bo admires two teachers."], "Does Bo admire two teachers?", "Yes"),
    (["Bo admires two teachers."], "Does Bo admire three teachers?", "Unknown"),
    (["Bo admires two teachers."], "Does Bo admire a teacher?", "Yes"),
    (["Ada owns 4 cats."], "How many cats does Ada own?", "4"),
    (["Tom owns one dog."], "How many dogs does Tom own?", "1"),
    (["Bo admires two teachers.", "Bo admires a teacher."], "How many teachers does Bo admire?", "3"),
    ([], "How many cats does Zed own?", "0"),
    (["Two cats sleep."], "How many cats sleep?", "2"),
    (["Ada owns 4 cats.", "Ada owns 4 cats."], "How many cats does Ada own?", "4"),
])
def test_other_words(told: list[str], question: str, answer: str) -> None:
    m = Mind()
    for s in told:
        m.tell(s)
    assert first(m, question) == answer


@pytest.mark.parametrize("text", [
    "Every bike has three wheels.", "Kim owns more than two cats.", "Kim owns most cats.", "Kim owns half of the cats.",
])
def test_what_stays_refused(mind: Mind, text: str) -> None:
    assert mind.hear(text).outcome == "refused"

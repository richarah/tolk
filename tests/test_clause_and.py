"""Item 6: "Kim sings and Sandy dances." is two statements, each with a sentence of its own."""

from tolk.mind import Mind


def test_a_clause_and_is_two_statements_and_the_reply_counts_the_facts() -> None:
    m = Mind()
    r = m.tell("Kim sings and Sandy dances.")
    assert r.outcome == "stored, 2 new fact(s)"
    assert r.printed == "tell   _sing_v_1(e1, kim)\ntell   _dance_v_1(e2, sandy)"
    assert m.db.execute("SELECT COUNT(*) FROM sentence").fetchone() == (2,)


def test_one_of_them_can_be_forgotten_and_the_other_stays() -> None:
    m = Mind()
    m.tell("Kim sings and Sandy dances.")
    assert m.hear("Forget that Kim sings.").outcome.startswith("forgot")
    assert m.ask("Does Kim sing?").outcome == "Unknown"
    assert m.ask("Does Sandy dance?").outcome.startswith("Yes")


def test_a_contradiction_in_one_refuses_both() -> None:
    m = Mind()
    m.tell("Sandy dances.")
    r = m.tell("Kim sings and Sandy does not dance.")
    assert r.outcome.startswith("refused, contradicts")
    assert m.ask("Does Kim sing?").outcome == "Unknown"


def test_what_one_event_says_stays_one_statement() -> None:
    m = Mind()
    m.tell("Ben teaches math.")
    assert m.db.execute("SELECT COUNT(*) FROM sentence").fetchone() == (1,)
    m.tell("Kim sings and Kim dances.")
    assert m.db.execute("SELECT COUNT(*) FROM sentence").fetchone() == (3,)

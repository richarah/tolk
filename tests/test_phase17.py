"""Phase 17: the public interface. Expected printed forms were written from the shapes in SPEC.md and the earlier phases."""

import pytest

import tolk


def test_exactly_these_names_are_public() -> None:
    assert sorted(tolk.__all__) == sorted([
        "read", "printed", "Mind", "LF", "Tell", "Rule", "Ask", "Same", "Describe", "Refusal", "Atom", "Const", "Var"])
    for name in tolk.__all__:
        assert hasattr(tolk, name)


@pytest.mark.parametrize("text, form", [
    ("Rio is a sparrow.", "tell   _sparrow_n_1(rio)"),
    ("Every sparrow is a finch.", "rule   _finch_n_1(X) :- _sparrow_n_1(X)"),
    ("Does Rio swim?", "ask    _swim_v_1(E, rio)"),
    ("Who admires Bo?", "ask X  _admire_v_1(E, X, bo)"),
    ("Is Rio a finch?", "ask    _finch_n_1(rio)"),
    ("Bruce Wayne is Batman.", "same   bruce_wayne = batman"),
    ("Who is Rio?", "describe rio"),
    ("How many cats does Ada own?", "count X  _cat_n_1(X), _own_v_1(E, ada, X)"),
    ("Ada does not like cats.", "rule   not _like_v_1(_, ada, X) :- _cat_n_1(X)"),
    ("If Rio hums, Ada is calm.", "rule   _calm_a_1(E!, ada) :- _hum_v_1(E1, rio)"),
])
def test_read_gives_the_logical_form_without_a_store(text: str, form: str) -> None:
    assert tolk.printed(tolk.read(text)) == form


def test_read_returns_a_refusal_and_does_not_raise() -> None:
    x = tolk.read("Lee wants Kim to sing.")  # object control: a control verb with its own subject is refused (subject control is a claim)
    assert isinstance(x, tolk.Refusal) and x.code == "UNSUPPORTED_PREDICATE"
    assert isinstance(tolk.read(""), tolk.Refusal)


def test_known_predicates_steer_the_reading_by_name_or_by_name_and_arity() -> None:
    plain = tolk.printed(tolk.read("Sam works in Paris."))
    by_name = tolk.printed(tolk.read("Sam works in Paris.", frozenset({"_work_v_in"})))
    by_pair = tolk.printed(tolk.read("Sam works in Paris.", frozenset({("_work_v_in", 3)})))
    assert plain != by_name and by_name == by_pair == "tell   _work_v_in(e1, sam, paris)"


def test_mind_is_the_same_class() -> None:
    assert tolk.Mind().tell("Rio is a sparrow.").outcome.startswith("stored")


def test_a_pronoun_or_a_definite_without_a_store_is_refused() -> None:
    assert isinstance(tolk.read("The dog barks."), tolk.Refusal)
    assert isinstance(tolk.read("It sings."), tolk.Refusal)

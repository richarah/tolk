from tolk import lf
from tolk.lf import Atom, Const, Var


def test_rule_creates_head_variables_the_body_does_not_bind() -> None:
    rule = lf.Rule(
        head=(Atom("_have_v_1", (Var("e2"), Var("x3"), Var("x8"))),),
        body=(Atom("_dog_n_1", (Var("x3"),)),),
    )
    assert rule.creates == (Var("e2"), Var("x8"))


def test_show_marks_created_thing_once() -> None:
    rule = lf.Rule(
        head=(Atom("_have_v_1", (Var("e2"), Var("x3"), Var("x8"))), Atom("_owner_n_of", (Var("x8"),))),
        body=(Atom("_dog_n_1", (Var("x3"),)),),
    )
    assert lf.show(rule) == "rule   _have_v_1(E!, X, Y!), _owner_n_of(Y) :- _dog_n_1(X)"


def test_printed_forms_follow_spec_shapes() -> None:
    assert lf.show(lf.Tell((Atom("_robin_n_1", (Const("tweety"),)),))) == "tell   _robin_n_1(tweety)"
    assert lf.show(lf.Ask((Atom("_like_v_1", (Var("e2"), Var("x3"), Const("sandy"))),), (Var("x3"),))) == (
        "ask X  _like_v_1(E, X, sandy)"
    )
    assert lf.show(lf.Same(Const("clark_kent"), Const("superman"))) == "same   clark_kent = superman"
    assert lf.show(lf.Refusal("NEGATION_IN_RULE_HEAD", "x")) == "refuse NEGATION_IN_RULE_HEAD: x"

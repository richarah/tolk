"""Phase 24: wording through the grammar. Expectations were written before the code, except the counts, which are pasted from the run."""

import json
import sys

import pytest

from helpers import ROOT
from tolk import generate
from tolk.mind import Mind

TIER_A = [
    "Tweety is a robin.", "Every robin is a bird.", "Every bird flies.", "Birds are animals.",
    "Tweety sings.", "Every robin that sings is happy.", "Kim is a person.", "Kim owns a dog.",
    "Every person who owns a dog is happy.", "Kim likes Sandy.", "Rex is a dog.", "Every dog has an owner.",
]


def worded(m: Mind, pred: str, *args: str) -> generate.Wording:
    marks = " AND ".join(f"a{i} = ?" for i in range(len(args)))
    (fid,) = m.db.execute(f"SELECT id FROM fact WHERE pred = ? AND {marks or '1'}", (pred, *args)).fetchone()
    return m.word(fid)


def test_the_skeletons_are_what_the_script_makes_from_the_fixtures() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import skeletons
    assert skeletons.build() == generate.SKELETONS


def test_every_pattern_has_a_skeleton() -> None:
    assert set(generate.SKELETONS) == {"verb1", "verb2", "noun", "adj", "not_verb1", "not_verb2", "not_noun", "not_adj"}


def test_the_tier_a_derived_facts_are_generated_or_counted_as_templates() -> None:
    m = Mind()
    for s in TIER_A:
        m.tell(s)
    out = [(m.db.execute("SELECT pred FROM fact WHERE id = ?", (fid,)).fetchone()[0], m.word(fid))
           for (fid,) in m.db.execute("SELECT id FROM fact WHERE level >= 2 ORDER BY id")]
    generated = [(p, w.text) for p, w in out if w.how == "generated"]
    templates = [p for p, w in out if w.how == "template"]
    assert len(generated) + len(templates) == len(out) == 9
    assert ("_bird_n_1", "Tweety is a bird.") in generated and ("_fly_v_1", "Tweety flies.") in generated
    assert len(generated) == 5 and len(templates) == 4, (generated, templates)


def test_the_one_place_verb_and_is_a_patterns_generate() -> None:
    m = Mind()
    m.tell("Tweety sings.")
    m.tell("Tweety is a robin.")
    assert worded(m, "_sing_v_1", "e1", "tweety") == ("Tweety sings.", "generated")
    assert worded(m, "_robin_n_1", "tweety") == ("Tweety is a robin.", "generated")


@pytest.mark.parametrize("told, pred, args, want", [
    ("Rio hums.", "_hum_v_1", ("e1", "rio"), "Rio hums."),
    ("Ada admires Bo.", "_admire_v_1", ("e1", "ada", "bo"), "Ada admires Bo."),
    ("Pip is a finch.", "_finch_n_1", ("pip",), "Pip is a finch."),
    ("Ada is cheerful.", "_cheerful_a_1", ("e1", "ada"), "Ada is cheerful."),
    ("Ada does not like Bo.", "_like_v_1", ("", "ada", "bo"), "Ada doesn't like Bo."),
    ("Pip does not swim.", "_swim_v_1", ("", "pip"), "Pip doesn't swim."),
    ("Pip is not a bird.", "_bird_n_1", ("pip",), "Pip isn't a bird."),
    ("Ada is not cheerful.", "_cheerful_a_1", ("", "ada"), "Ada isn't cheerful."),
    ("Bo sleeps.", "_sleep_v_1", ("e1", "bo"), "Bo sleeps."),
    ("Cy owns Rex.", "_own_v_1", ("e1", "cy", "rex"), "Cy owns Rex."),
])
def test_own_word_facts_are_worded_through_the_grammar(told: str, pred: str, args: tuple, want: str) -> None:
    m = Mind()
    m.tell(told)
    w = worded(m, pred, *args)
    assert w.text == want and w.how == "generated"


def test_an_unknown_word_has_no_entry_in_the_generator_so_the_template_is_marked() -> None:
    m = Mind()
    m.tell("Pip is a blorp.")
    assert worded(m, "_blorp_n_unknown", "pip") == ("pip is a blorp", "template")


def test_a_thing_that_has_no_name_gets_the_template() -> None:
    m = Mind()
    m.tell("Kim owns a dog.")
    assert worded(m, "_dog_n_1", "a1").how == "template"


def test_a_sentence_that_does_not_give_the_fact_back_is_not_kept() -> None:
    from tolk import store
    known = store.known_preds(Mind().db)
    assert generate._gives_back("Tweety sings.", "_sing_v_1", ["tweety"], True, known)
    assert not generate._gives_back("Tweety sings.", "_dance_v_1", ["tweety"], True, known)
    assert not generate._gives_back("Tweety sings.", "_sing_v_1", ["tweety"], False, known)
    assert not generate._gives_back("Tweety sings.", "_sing_v_1", ["kim"], True, known)


def test_the_shortest_wins_and_the_first_alphabetically_among_equals() -> None:
    assert generate.pick({"Pingu does not fly.", "Pingu doesn't fly."}) == "Pingu doesn't fly."
    assert generate.pick({"Sandy is liked by Kim.", "Kim likes Sandy."}) == "Kim likes Sandy."
    assert generate.pick({"Bo sings.", "Ao sings."}) == "Ao sings."
    assert generate.pick(set()) is None

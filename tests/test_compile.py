"""Tier A: the printed form of the chosen reading, checked against the table below.

The expected strings were written from the printed-form shapes in SPEC.md and the
predicate names in the fixtures, not from the output of compile.py.
"""

import ast
import io
import json
import re
import tokenize

import pytest

from helpers import ROOT, fixture_path
from tolk import compile as comp
from tolk import lf, say, sem

EXPECTED = {
    "Tweety is a robin.": "tell   _robin_n_1(tweety)",
    "Every robin is a bird.": "rule   _bird_n_1(X) :- _robin_n_1(X)",
    "Every bird flies.": "rule   _fly_v_1(E!, X) :- _bird_n_1(X)",
    "Birds are animals.": "default _animal_n_1(X) :- _bird_n_1(X)",
    "Tweety sings.": "tell   _sing_v_1(e1, tweety)",
    "Every robin that sings is happy.": "rule   _happy_a_with(E!, X) :- _robin_n_1(X), _sing_v_1(E1, X)",
    "Kim is a person.": "tell   _person_n_1(kim)",
    "Kim owns a dog.": "tell   _own_v_1(e1, kim, a1)\ntell   _dog_n_1(a1)",
    "Every person who owns a dog is happy.": "rule   _happy_a_with(E!, X) :- _person_n_1(X), _own_v_1(E1, X, Y), _dog_n_1(Y)",
    "Kim likes Sandy.": "tell   _like_v_1(e1, kim, sandy)",
    "Rex is a dog.": "tell   _dog_n_1(rex)",
    "Every dog has an owner.": "rule   _have_v_1(E!, X, Y!), _owner_n_of(Y) :- _dog_n_1(X)",
    "Does Tweety fly?": "ask    _fly_v_1(E, tweety)",
    "Is Tweety a bird?": "ask    _bird_n_1(tweety)",
    "Is Tweety an animal?": "ask    _animal_n_1(tweety)",
    "Is Tweety happy?": "ask    _happy_a_with(E, tweety)",
    "What flies?": "ask X  _fly_v_1(E, X)",
    "Which robin sings?": "ask X  _robin_n_1(X), _sing_v_1(E, X)",
    "Who is happy?": "ask X  _happy_a_with(E, X)",
    "Who likes Sandy?": "ask X  _like_v_1(E, X, sandy)",
    "Who does Kim like?": "ask X  _like_v_1(E, kim, X)",
    "Is Sandy happy?": "ask    _happy_a_with(E, sandy)",
    "Does Rex have an owner?": "ask    _have_v_1(E, rex, X), _owner_n_of(X)",
}

TIER_A = [
    line for line in (ROOT / "tests" / "sentences.txt").read_text().split("# tier B")[0].splitlines()
    if line.strip() and not line.startswith("#")
]
TIER_B_AND_C = [
    line for line in (ROOT / "tests" / "sentences.txt").read_text().split("# tier B")[1].splitlines()
    if line.strip() and not line.startswith("#")
]

LEMMA = re.compile(r"^_([a-z]+)_[nva](?:_|\d|$)")
# Determiners and auxiliaries the grammar names as ordinary predicates. Quantifier names
# are allowed in rules by SPEC rule 3, and the copula is recognised by its sense suffix.
FUNCTION_LEMMAS = {"do", "does", "doe", "every", "is", "no", "a", "an", "the", "be", "i"}


def compiled(text: str) -> str:
    record = json.loads(fixture_path(text).read_text())
    readings = [sem.read(r["simplemrs"], r["lexical"]) for r in record["readings"]]
    index, x = comp.choose(readings, set())
    return lf.show(x)


def test_table_covers_tier_a() -> None:
    assert sorted(EXPECTED) == sorted(TIER_A)


@pytest.mark.parametrize("text", TIER_A)
def test_printed_form(text: str) -> None:
    assert compiled(text) == EXPECTED[text]


def content_lemmas() -> set[str]:
    """Lemmas of the sentences in tests/sentences.txt, the set SPEC phase 1 names. Extra sentences are not scanned."""
    out: set[str] = set()
    for text in TIER_A + TIER_B_AND_C:
        for reading in json.loads(fixture_path(text).read_text())["readings"]:
            for ep in reading["neutral"]["eps"]:
                match = LEMMA.match(ep["pred"])
                if match and not ep["pred"].endswith("_v_id"):
                    out.add(match.group(1))
                if "CARG" in ep["args"]:
                    out.add(ep["args"]["CARG"].lower())
    return out - FUNCTION_LEMMAS


def code_words(source: str, allowed: frozenset[str] = frozenset()) -> set[str]:
    """Words in the code of a module: comments and docstrings are prose, and rule 3 is about what the rules key on. Every string is
    scanned, except one that is exactly an entry of `allowed`, which only say.py's own list may be."""
    out: set[str] = set()
    previous = tokenize.NEWLINE
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        docstring = tok.type == tokenize.STRING and previous in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.NL)
        listed = tok.type == tokenize.STRING and ast.literal_eval(tok.string) in allowed
        if tok.type not in (tokenize.COMMENT, tokenize.NL) and not docstring and not listed:
            out |= set(re.split(r"[^a-z]+", tok.string.lower()))
        if tok.type != tokenize.COMMENT:
            previous = tok.type
    return out


def test_the_scan_reads_every_string_except_an_exact_entry_of_the_allowed_list() -> None:
    assert "sparrow" in code_words('x = "among those sparrow"')
    assert not code_words('x = "among those sparrow"', frozenset({"among those sparrow"})) & {"sparrow"}
    assert "sparrow" in code_words('x = "among those sparrow, too"', frozenset({"among those sparrow"}))


def test_the_scan_ignores_comments_and_docstrings_but_not_code() -> None:
    source = '"""Docstring about robins."""\n\n\ndef f():\n    """Another about birds."""\n    x = "sparrow"  # a comment about finches\n    return x\n'
    assert code_words(source) >= {"sparrow", "def", "return"} and not code_words(source) & {"robins", "birds", "finches", "docstring", "comment"}


def test_source_has_no_content_lemma() -> None:
    lemmas = content_lemmas()
    assert lemmas, "no lemmas found in fixtures"
    offenders = []
    for path in (ROOT / "tolk").rglob("*.py"):
        allowed = say.WORDING if path.name == "say.py" else frozenset()
        offenders += [f"{path.relative_to(ROOT)}: {w}" for w in sorted(code_words(path.read_text(), allowed) & lemmas)]
    assert offenders == []


def test_the_allowed_wording_is_kept_in_say_py_and_nowhere_else() -> None:
    for path in (ROOT / "tolk").rglob("*.py"):
        if path.name != "say.py":
            assert not [w for w in say.WORDING if w in path.read_text()], path


TIER_C_FORMS = {
    "Kim lives in Oslo.": "tell   _live_v_1(e1, kim)\ntell   _in_p_loc(e1, oslo)",
    "Sandy arrived.": "tell   _arrive_v_1(e1, sandy)\ntell   tense(e1, past)",
    "Who lives in Oslo?": "ask X  _live_v_1(E, X), _in_p_loc(E, oslo)",
    "Where does Kim live?": "ask X  _*_p_[ls]*(E, X), _live_v_1(E, kim)",
}


@pytest.mark.parametrize("text", list(TIER_C_FORMS))
def test_tier_c_printed_form(text: str) -> None:
    assert compiled(text) == TIER_C_FORMS[text]

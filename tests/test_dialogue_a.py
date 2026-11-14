import subprocess
import sys
from pathlib import Path

import pytest

from tolk import say
from tolk.ask import UNKNOWN, YES, Proof
from tolk.mind import Mind

ROOT = Path(__file__).resolve().parent.parent

STATEMENTS = [
    "Tweety is a robin.", "Every robin is a bird.", "Every bird flies.", "Birds are animals.",
    "Tweety sings.", "Every robin that sings is happy.", "Kim is a person.", "Kim owns a dog.",
    "Every person who owns a dog is happy.", "Kim likes Sandy.", "Rex is a dog.", "Every dog has an owner.",
]

# Question, value, and the answer text. The wording is from the spec table.
QUESTIONS = [
    ("Does Tweety fly?", YES, "Yes"),
    ("Is Tweety an animal?", YES, "Yes"),
    ("Is Tweety happy?", YES, "Yes"),
    ("What flies?", YES, "Tweety"),
    ("Which robin sings?", YES, "Tweety"),
    ("Who is happy?", YES, "Kim and Tweety"),
    ("Who likes Sandy?", YES, "Kim"),
    ("Who does Kim like?", YES, "Sandy"),
    ("Is Sandy happy?", UNKNOWN, "Unknown"),
    ("Does Rex have an owner?", YES, "Yes"),
]


@pytest.fixture(scope="module")
def mind() -> Mind:
    m = Mind()
    for s in STATEMENTS:
        m.tell(s)
    return m


@pytest.mark.parametrize("question,value,text", QUESTIONS)
def test_dialogue_answers(mind: Mind, question: str, value: str, text: str) -> None:
    result = mind.ask(question)
    assert result.answer.value == value
    assert say.answer_text(mind.db, result.answer) == text


def leaves(p: Proof) -> list[Proof]:
    return [p] if not p.premises else [leaf for q in p.premises for leaf in leaves(q)]


def depth(p: Proof) -> int:
    return 1 + max((depth(q) for q in p.premises), default=0)


def test_yes_proofs_have_told_leaves(mind: Mind) -> None:
    a = mind.ask("Does Tweety fly?").answer
    told = [leaf for proofs in a.proofs for p in proofs for leaf in leaves(p)]
    assert told and all(leaf.sentence is not None and not leaf.premises for leaf in told)


def test_fly_proof_has_three_steps(mind: Mind) -> None:
    a = mind.ask("Does Tweety fly?").answer
    assert depth(a.proofs[0][0]) == 3


def test_repl_prints_reading_form_and_result() -> None:
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "repl.py")],
        input="Tweety is a robin.\nIs Tweety a robin?\nWho lives in Oslo?\n",
        capture_output=True, text=True, timeout=600,
    ).stdout
    lines = out.splitlines()
    assert lines[1].strip() == "reading 1 of 2"
    assert lines[2].strip() == "tell   _robin_n_1(tweety)"
    assert "Yes" in out
    assert any(line.strip().startswith("reading ") for line in lines[3:])

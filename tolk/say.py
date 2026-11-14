"""Plain wording for facts and proofs. Stiff by design: a fact is shown as its predicate and arguments, never inflected."""

import sqlite3
from tolk.ask import Answer, Proof


def fact_text(db: sqlite3.Connection, fact_id: int) -> str:
    pred, a0, a1, a2, positive = db.execute(
        "SELECT pred, a0, a1, a2, positive FROM fact WHERE id = ?", (fact_id,)
    ).fetchone()
    neg = "" if positive else "not "
    if not pred.startswith("_"):
        return f"{neg}{pred}({', '.join(a for a in (a0, a1, a2) if a)})"
    lemma, pos = pred.lstrip("_").split("_")[:2]
    if pos == "n":
        things = [a for a in (a0, a1, a2) if a]
        if len(things) == 1 and positive:
            article = "an" if lemma[0] in "aeiou" else "a"
            return f"{things[0]} is {article} {lemma}"
        return f"{neg}{lemma}({', '.join(things)})"
    # Verbs, adjectives and prepositions take their event first; the event is not shown.
    things = [a for a in (a1, a2) if a]
    return f"{neg}{lemma}({', '.join(things)})"


def proof_text(db: sqlite3.Connection, p: Proof, depth: int = 0) -> str:
    pad = "  " * depth
    if p.sentence is not None:
        (text,) = db.execute("SELECT text FROM sentence WHERE id = ?", (p.sentence,)).fetchone()
        line = f'{pad}{fact_text(db, p.fact)}  (told: "{text}")'
    else:
        line = f"{pad}{fact_text(db, p.fact)}  (by rule {p.rule})"
    return "\n".join([line] + [proof_text(db, q, depth + 1) for q in p.premises])


def answer_text(db: sqlite3.Connection, a: Answer) -> str:
    if a.value != "Yes" or not a.solutions:
        return a.value
    names = [_name(v) for solution in a.solutions for v in solution]
    if len(names) <= 2:
        return " and ".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def _name(value: str) -> str:
    return value.replace("_", " ").title()


def proposal_text(p_pred: str, q_pred: str) -> str:
    return f"Is every {_lemma(p_pred)} a {_lemma(q_pred)}?"


def _lemma(pred: str) -> str:
    return pred.lstrip("_").split("_")[0]

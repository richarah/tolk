"""Plain wording for facts and proofs. Stiff by design: a fact is shown as its predicate and arguments, never inflected."""

import sqlite3
from tolk import settings
from tolk.ask import Answer, Proof


# The user is spoken to as "you" and tolk speaks as "I".
SPEAKERS = {"user": "you", "tolk": "I"}
COPULA = {"you": "are", "I": "am"}
# Wording that contains a word the rules also use as a predicate. The content-word scan reads every string in tolk/ except these exact ones.
AMONG_THOSE = " (among those I know)"
WORDING = frozenset({AMONG_THOSE})


def fact_text(db: sqlite3.Connection, fact_id: int) -> str:
    pred, a0, a1, a2, positive = (SPEAKERS.get(v, v) if not isinstance(v, str) or not v.startswith("claim") else claim_text(db, v)
                                   for v in db.execute("SELECT pred, a0, a1, a2, positive FROM fact WHERE id = ?", (fact_id,)).fetchone())
    neg = "" if positive else "not "
    if not pred.startswith("_"):
        return f"{neg}{pred}({', '.join(a for a in (a0, a1, a2) if a)})"
    lemma, pos = pred.lstrip("_").split("_")[:2]
    if pos == "n":
        things = [a for a in (a0, a1, a2) if a]
        if len(things) == 1 and positive:
            article = "an" if lemma[0] in "aeiou" else "a"
            return f"{things[0]} {COPULA.get(things[0], 'is')} {article} {lemma}"
        return f"{neg}{lemma}({', '.join(things)})"
    # Verbs, adjectives and prepositions take their event first; the event is not shown. A negative fact shows the tense, modal and
    # progressive of its event, because it denies only that: "not sing(kim) [past]" does not deny that Kim sings.
    things = [a for a in (a1, a2) if a]
    return f"{neg}{lemma}({', '.join(things)}){'' if positive else _marks(db, a0)}"


def _marks(db: sqlite3.Connection, event: str) -> str:
    if not event:
        return ""
    marks = [v for (v,) in db.execute("SELECT a1 FROM fact WHERE pred = 'tense' AND a0 = ? AND positive = 1 ORDER BY a1", (event,))]
    marks += [v for (v,) in db.execute("SELECT a1 FROM fact WHERE pred = 'modal' AND a0 = ? AND positive = 1 ORDER BY a1", (event,))]
    return f" [{', '.join(dict.fromkeys(marks))}]" if marks else ""


def fact_line(db: sqlite3.Connection, fact_id: int) -> str:
    """A fact as a proof or an answer shows it: through the grammar when the wording setting says so, and per fact the template when
    the grammar does not give the fact back."""
    if settings.get(db, "wording") == "generated":
        from tolk import generate  # generate words with the template as its fallback, so it imports this module
        return generate.word(db, fact_id).text
    return fact_text(db, fact_id)


def claim_text(db: sqlite3.Connection, claim: str) -> str:
    """What a claim holds, worded, as it stands in the context of the claim."""
    ids = [i for (i,) in db.execute("SELECT id FROM fact WHERE ctx = ? ORDER BY id", (claim,))]
    return "[" + "; ".join(fact_text(db, i) for i in ids) + "]" if ids else claim


def proof_text(db: sqlite3.Connection, p: Proof, depth: int = 0) -> str:
    pad = "  " * depth
    if p.sentence is not None:
        (text,) = db.execute("SELECT text FROM sentence WHERE id = ?", (p.sentence,)).fetchone()
        line = f'{pad}{fact_line(db, p.fact)}  (told: "{text}")'
    else:
        (source,) = db.execute("SELECT s.text FROM rule r JOIN sentence s ON s.id = r.sentence WHERE r.id = ?", (p.rule,)).fetchone()
        by = f"by built-in axiom: {source[len('[axiom] '):]}" if source.startswith("[axiom] ") else f"by rule {p.rule}"
        line = f"{pad}{fact_line(db, p.fact)}  ({by})"
    return "\n".join([line] + [proof_text(db, q, depth + 1) for q in p.premises])


def answer_text(db: sqlite3.Connection, a: Answer) -> str:
    if a.count is not None:
        return str(a.count)
    if a.value != "Yes" or not a.solutions:
        return a.value
    names = [_name(v) for solution in a.solutions for v in solution]
    if len(names) <= 2:
        return " and ".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def _name(value: str) -> str:
    if "(" in value or value.startswith("["):
        return value  # a claim, already worded
    return SPEAKERS.get(value) or value.replace("_", " ").title()


def proposal_text(p_pred: str, q_pred: str) -> str:
    return f"Is every {_lemma(p_pred)} a {_lemma(q_pred)}?"


def _lemma(pred: str) -> str:
    return pred.lstrip("_").split("_")[0]

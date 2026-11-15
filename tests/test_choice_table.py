"""The reading-choice table (tests/choice_table.json, built by scripts/choice_table.py from the fixtures and the stores the dialogues chose in).
Each row is a sentence whose chosen reading is not the parser's first, or where a refusal passed a tie on. The table is a test: the order
of criteria must still choose the recorded reading in every row, and the measures must still be the recorded ones."""

import json
import sys

import pytest

from helpers import ROOT, readings_of
from tolk import choice, compile as comp

ROWS = json.loads((ROOT / "tests" / "choice_table.json").read_text())


def known(row: dict) -> set:
    return {tuple(p) for p in row["known"]}


@pytest.mark.parametrize("row", ROWS, ids=[f"{r['text']} [{len(r['known'])}]" for r in ROWS])
def test_the_order_chooses_the_recorded_reading(row: dict) -> None:
    readings = readings_of(row["text"])
    assert comp.choose(readings, known(row))[0] + 1 == row["chosen"]
    for r in row["readings"]:
        if "generic" in r:
            assert choice.measures(readings, r["rank"] - 1, known(row)) == (r["generic"], r["overlap"], r["swallowed"])


@pytest.mark.parametrize("row", [r for r in ROWS if r["decided_by"] == "criteria"], ids=lambda r: r["text"])
def test_a_row_decided_by_the_criteria_has_no_reading_before_the_chosen_one_that_ties_with_it(row: dict) -> None:
    readings = readings_of(row["text"])
    assert choice.preferred(readings, known(row))[0] + 1 == row["chosen"]


def test_the_table_is_the_one_the_script_builds() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import choice_table
    assert choice_table.build() == ROWS


def test_the_table_has_the_rows_that_matter() -> None:
    texts = {r["text"] for r in ROWS}
    assert {"Fish do not fly.", "Kim does not like fish.", "Sam works in Paris.", "Does Kim know that Rio flies.".replace(".", "?"), "Who is a bird?"} <= texts

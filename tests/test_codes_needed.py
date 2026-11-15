"""Item 5: each of three reading-refusal codes changes a row of the choice table when it is removed, so each stays and DECISIONS.md names
the fixtures that need it."""

import sys

import pytest

from helpers import ROOT, fixture_path

sys.path.insert(0, str(ROOT / "scripts"))
import code_removal  # noqa: E402

DECISIONS = (ROOT / "DECISIONS.md").read_text()


@pytest.mark.parametrize("code", ["FALLBACK_PARSE", "GRAMMAR_ARTIFACT", "DEMONSTRATIVE"])
def test_removing_the_code_changes_a_row_and_decisions_names_the_fixtures(code: str) -> None:
    rows = code_removal.changed(code)
    assert rows
    section = DECISIONS.split(f"### {code}", 1)[1].split("###", 1)[0].split("## ", 1)[0]
    for text in {r[0] for r in rows}:
        assert fixture_path(text).name in section, (code, text)

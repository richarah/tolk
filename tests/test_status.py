"""STATUS.md names every refusal code and every setting."""

from helpers import ROOT
from tolk import lf, settings

TEXT = (ROOT / "STATUS.md").read_text()


def test_every_refusal_code_is_in_status() -> None:
    import re
    missing = [c for c in lf.REFUSALS if c not in TEXT and not any(c.startswith(stem) and c.endswith(("_SUBJECT", "_OBJECT", "_ASPECT", "_FORCE", "_PREDICATE", "_QUANTIFIER", "_TENSE")) and stem in TEXT for stem in re.findall(r"[A-Z]+_[A-Z]+(?= / )|UNEXPRESSED|UNSUPPORTED", TEXT))]
    assert missing == []


def test_every_setting_is_in_status() -> None:
    assert all(f"`{k}`" in TEXT for k in settings.ALLOWED) and "`policy`" in TEXT and "`auto_revise`" in TEXT

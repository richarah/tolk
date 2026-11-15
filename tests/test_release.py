"""Release hygiene: nothing large or downloaded is committed, and the ignore rules keep it that way."""

import subprocess

from helpers import ROOT

IGNORED = ["erg/", ".venv/", "*.dat", "*.dat.bz2", "spider/", "*.db", "*.sqlite", ".env", "venv/", "dist/", "build/"]


def test_the_ignore_rules_name_the_grammar_the_parser_the_spider_data_and_environments() -> None:
    lines = (ROOT / ".gitignore").read_text().splitlines()
    assert [p for p in IGNORED if p not in lines] == []


def test_no_tracked_file_is_large_or_a_download() -> None:
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    big = [f for f in files if f and (ROOT / f).exists() and (ROOT / f).stat().st_size > 1_000_000]
    assert big == []
    assert [f for f in files if f.endswith((".dat", ".bz2", ".zip", ".tar", ".gz", ".db", ".sqlite")) or f.startswith(("erg/", ".venv/", "spider/"))] == []

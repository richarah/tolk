"""Housekeeping item 2: one workflow, on push and pull request, that fetches the parser and grammar (cached), installs and runs the suite."""

from helpers import ROOT

FILES = sorted((ROOT / ".github" / "workflows").glob("*.y*ml")) if (ROOT / ".github" / "workflows").exists() else []


def test_there_is_exactly_one_workflow() -> None:
    assert len(FILES) == 1


def test_it_runs_on_push_and_pull_request_and_does_the_four_steps() -> None:
    text = FILES[0].read_text()
    for needle in ("push:", "pull_request:", "actions/checkout@", "actions/cache@", "path: erg", "sh scripts/setup_erg.sh", "pip install", "pytest"):
        assert needle in text, needle
    assert text.index("actions/cache@") < text.index("scripts/setup_erg.sh") < text.index("pip install") < text.index("pytest")


def test_the_parser_directory_can_be_named_by_the_environment_for_an_installed_copy() -> None:
    import subprocess
    import sys
    out = subprocess.run([sys.executable, "-c", "from tolk import erg; print(erg.ACE)"], capture_output=True, text=True, check=True,
                         env={"TOLK_ERG_DIR": "/somewhere/erg", "PATH": ""}, cwd=ROOT)
    assert out.stdout.strip() == "/somewhere/erg/ace"

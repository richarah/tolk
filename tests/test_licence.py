"""Housekeeping item 1: tolk has an MIT licence, and pyproject.toml says so."""

import tomllib

from helpers import ROOT


def test_the_licence_file_is_mit_with_a_holder() -> None:
    text = (ROOT / "LICENSE").read_text()
    assert text.startswith("MIT License\n\nCopyright (c) ")
    assert "Permission is hereby granted, free of charge" in text
    assert text.splitlines()[2].split("Copyright (c) ")[1].split(" ", 1)[1].strip()  # a year, then a name


def test_pyproject_has_the_licence_field() -> None:
    assert tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["license"] == {"file": "LICENSE"} or \
        tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["license"] == "MIT"

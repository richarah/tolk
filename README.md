# tolk

Reads English statements, stores what they say with their source, and answers questions with proofs. No neural or statistical component at runtime.

Setup: `sh scripts/setup_erg.sh`, then `uv venv .venv && uv pip install -e '.[test]'`.

Run the tests with `.venv/bin/pytest -q`. Talk to it with `.venv/bin/python scripts/repl.py`.

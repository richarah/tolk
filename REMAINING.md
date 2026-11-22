# What remains

Written after the open-items pass (branch `open-items`, on top of the `v0.1.0` release). Each line says what is missing and why it matters.
Measured figures are from the commands named; older figures are not repeated here.

## Release state
- `v0.1.1` is tagged at `35bb73c` on `master`, which is the open-items pass. CI on `master` at that commit passed: 913 tests collected, 913 passed.
- SQUID is pinned to `v0.1.1` (commit `da93f47` on `tolk-backend` and `main`). From a fresh clone: 128 passed, 5 xfailed; the differential test agrees on 15 of 15. SQUID's tests need `TOLK_ERG_DIR` set to a checkout's `erg/`.
- tolk's `pyproject.toml` still says version 0.1.0 at the `v0.1.1` tag. Fixing it needs a new tag.

## Decisions the owner may want to reverse (DECISIONS.md, "Open-items pass")
- "Quorl is a thing." stores Quorl as a name. A word that should be a class needs the article.
- "Ola owns more than two cellos." is refused UNKNOWN_WORD, not the comparison, because unknown words are named first. The same sentence with a known noun
  is refused UNSUPPORTED_PREDICATE: more_comp.
- "Kim told Lee that Rio sings or hums." is refused TOO_MANY_ARGUMENTS, a message that does not say the sentence is about a claim. It was
  UNSUPPORTED_TENSE. The new tense rule lets a wrong reading through to a refusal that reads badly.

## Known limits (by design, or out of the SPEC's scope at the time; not all are permanent)
- Counting and numbers beyond the stated forms: "more than two" over a known noun is refused (more_comp). Cardinals in a rule and two numbers in a
  question are refused. (`scripts/coverage.py` lists the refusals; the largest in the four corpus files is `card`.)
- Modals, control verbs, durations, "most" and most quantifiers: refused as UNSUPPORTED_*.
- Progressive, past perfect and future perfect: refused (UNSUPPORTED_ASPECT). Past, future and present perfect are stored on the main event and on the clauses of an and or or; a past or future inside a claim is refused.
- Suppositions are one level deep.
- The reading choice does not rank parser senses ("Jo writes letters." reads `write_v_to`; "Bo bakes bread." reads the causative `bake`, the held-out miss). Needs a principled sense measure from the grammar, not a word list.
- "Kay" reads as "okay" (the grammar's word) and is refused UNKNOWN_WORD. Use another name.
- A name one edit from an accepted word is refused POSSIBLE_TYPO once, even when meant (the design; the user must resend it).

## Testing gaps
- Coverage of the grammar's own test suite and of its predicate inventory is not measured. Only the corpus files are measured:
  `scripts/coverage.py tests/sentences.txt tests/extra.txt tests/round1.txt tests/round2.txt` compiled 125 of 149 (83.9%) at the time of writing.
- Held-out check: 26 new sentences, 24 match (tests/heldout.py, DECISIONS.md). Two known misses: "Bo bakes bread." (sense) and "A penguin is a bird." (existential or generic).
  only measured set.
- The fuzz of 511 sentences with four mutations each (run during the open-items pass, not a committed test) is not in the suite. Its result is in
  the open-items commit message.
- Two verification rounds were the only independent checks; they are in VERIFY.md. Nothing has verified the open-items pass independently.

## Proofs and wording
- Proofs print the template wording, not the generated wording, in every earlier dialogue (PROGRESS.md, "What I would do next", item 1). Generated
  wording exists for tier A facts only (`tests/test_phase24.py`).

## Parser and grammar
- ACE 0.9.34 and ERG 2018 only, Linux x86-64 (scripts/setup_erg.sh). Other platforms need their own ACE build.
- Tagged input is a hint: an unknown word the tagged parse does not analyse falls back to the untagged parse (DECISIONS.md, vocabulary).
- Words the grammar has as names only ("tove") can be refused rather than learned.

## Continuous integration
- Moved to Node 24 action versions on branch `ci-node24` (checkout v7, setup-python v7, cache v6). Confirm the run before merging. The old workflow ran on Node 20 and printed a deprecation warning
  a deprecation warning (run 43737163813 on master).
- The erg cache is restored but not saved on a hit ("not saving cache" in the logs). That is correct, but a cache miss rebuilds it from the
  download address, which depends on sweaglesw.org being reachable.

## SQUID
- The legacy pipeline (`squid/legacy.py`, 121 lines) is kept, called from nowhere, and its five tests are expected failures (tests/legacy).
  Decide whether to delete it; the spec says leave it.
- Spider development set: 0 of 1034 questions produced SQL (benchmarks/spider_dev_2026-11-15.txt). Most refusals are imperatives and definite
  noun phrases. This is a scope result, not a tuning result; nothing was tuned.
- Values are read from the database only when the schema comes from SQLite. Spider JSON and SQLAlchemy schemas get no values, so the Ga fix
  does not apply to them.
- SQUID depends on tolk by git address, and the tolk repository is private: only its owner can install SQUID.
- The README's test count is written by hand (scripts/readme_numbers.py prints the current one). Re-run it after each change.

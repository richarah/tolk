# What remains

Written after the open-items pass (branch `open-items`, on top of the `v0.1.0` release). Each line says what is missing and why it matters.
Measured figures are from the commands named; older figures are not repeated here.

## Not released
- The open-items pass is on the `open-items` branch. It is not merged to `master` and not tagged. A release needs a tag (`v0.1.1`, say) and
  SQUID's dependency moved from `v0.1.0` to that tag. SQUID's `tolk-backend` branch and tests were run against `v0.1.0`, not against this pass.
- CI on `open-items` has not run yet at the time of writing (see the commit message and PROGRESS.md for the result if it has).

## Decisions the owner may want to reverse (DECISIONS.md, "Open-items pass")
- "Quorl is a thing." stores Quorl as a name. A word that should be a class needs the article.
- "Ola owns more than two cellos." is refused UNKNOWN_WORD, not the comparison, because unknown words are named first. The same sentence with a known noun
  is refused UNSUPPORTED_PREDICATE: more_comp.
- "Kim told Lee that Rio sings or hums." is refused TOO_MANY_ARGUMENTS, a message that does not say the sentence is about a claim. It was
  UNSUPPORTED_TENSE. The new tense rule lets a wrong reading through to a refusal that reads badly.

## Known limits, by design or by SPEC scope
- Counting and numbers beyond the stated forms: "more than two" over a known noun is refused (more_comp). Cardinals in a rule and two numbers in a
  question are refused. (`scripts/coverage.py` lists the refusals; the largest in the four corpus files is `card`.)
- Modals, control verbs, durations, "most" and most quantifiers: refused as UNSUPPORTED_*.
- Future, perfect and progressive tense: refused. Past is stored only on the main event and on the clauses of an and or or.
- Rules and identity merges inside a supposition: refused, because the rule and merge tables have no context column.
- Negation as failure is evaluated round by round; a strata-by-strata evaluation is not built (PROGRESS.md, Open).
- Repeated statements are recognised only when the text is identical. Two wordings of one meaning add facts.
- Definite referents that are anonymous are recorded with kind `named`.
- The reading choice does not rank parser senses ("Jo writes letters." reads `write_v_to`).
- "Kay" reads as "okay" (the grammar's word) and is refused UNKNOWN_WORD. Use another name.
- A name one edit from an accepted word is refused POSSIBLE_TYPO once, even when meant (the design; the user must resend it).

## Testing gaps
- Coverage of the grammar's own test suite and of its predicate inventory is not measured. Only the corpus files are measured:
  `scripts/coverage.py tests/sentences.txt tests/extra.txt tests/round1.txt tests/round2.txt` compiled 125 of 149 (83.9%) at the time of writing.
- The held-out check of the reading choice (stores the tests never build) is not done. The choice table in `tests/choice_table.json` is the
  only measured set.
- The fuzz of 511 sentences with four mutations each (run during the open-items pass, not a committed test) is not in the suite. Its result is in
  the open-items commit message.
- Two verification rounds were the only independent checks; they are in VERIFY.md. Nothing has verified the open-items pass independently.

## Proofs and wording
- Proofs print the template wording, not the generated wording, in every earlier dialogue (PROGRESS.md, "What I would do next", item 1). Generated
  wording exists for tier A facts only (`tests/test_phase24.py`).
- Proof lines for "Yes, by default" and "No, by default" name the rule but not the defeat that made it default-only, except through `defeated`.

## Parser and grammar
- ACE 0.9.34 and ERG 2018 only, Linux x86-64 (scripts/setup_erg.sh). Other platforms need their own ACE build.
- Tagged input is a hint: an unknown word the tagged parse does not analyse falls back to the untagged parse (DECISIONS.md, vocabulary).
- Words the grammar has as names only ("tove") can be refused rather than learned.

## Continuous integration
- The workflow uses actions/cache@v4, actions/checkout@v4 and actions/setup-python@v5, which run on Node 20 and print a deprecation warning
  (run 43737163813 on master). Upgrading them is needed before the runner removes Node 20.
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

# What remains

Current state after the medium-items pass (v0.1.2), the modals, control-verb, proofs and persistence items on `modals-and-next`. Each
item says what is missing and why. Figures are from the commands named.

## Release state
- `master` is at v0.1.2 (`41b5de3`): CI on the local self-hosted runner, 959 tests passed.
- Since then, `modals-and-next` (not merged, not tagged): modals, proofs wording, control verbs, persistence. Its suite: see the last commit.
- SQUID is pinned to v0.1.2 on `main` (`71aa3c6`): 128 passed, 5 xfailed; the differential test agrees on 15 of 15.
- CI runs on `[self-hosted, local]`: the hosted runners were blocked by billing. The runner process must be running for pushes to be tested.

## Decisions the owner may want to reverse (DECISIONS.md)
- "Quorl is a thing." stores Quorl as a name (open-items pass).
- "Ola owns more than two cellos." is refused for the unknown word, not as a comparison (open-items pass).
- Generated wording is the default for proofs (proofs item). The template is the fallback, marked.
- Subject control is a claim: "Kim wants to sing." is a claim the subject has (control item).
- Present perfect is stored as a past event, because the store has no "now" (M3).

## Refused by design or out of scope
- Object control: "Lee wants Kim to sing." is refused (UNSUPPORTED_PREDICATE): the infinitive has another subject.
- Claims inside a supposition: refused, as before (tests/test_phase21.py).
- Past perfect, future perfect: refused (UNSUPPORTED_ASPECT). A past or future inside a claim is refused (UNSUPPORTED_TENSE).
- A modal in a rule: refused. A negated modal ("cannot", "must not"), a negated progressive and a negated tense are stored with their own event, so they keep their tense, modal and progressive (DECISIONS.md, negated events).
- "Most cats purr.": refused. A proportion cannot be a Horn rule; a sound treatment needs counting, which SPEC.md puts out of scope.
- Counting and numbers: "more than two cats" over a known noun is refused (more_comp); cardinals in a rule, and two numbers in a question.
- Durations ("slept for two hours"): refused. They need a measure, which goes with counting.
- Suppositions are one level deep.

## Limits of the reading choice
- Parser senses are the grammar's: "Bo bakes bread." offers only the causative sense that compiles; "Jo writes letters." offers only `write_v_to`
  (DECISIONS.md, parser senses). Nothing for the choice to rank.
- Held-out check: 26 sentences, 24 match (`tests/heldout.py`). The two misses are the sense case above and "A penguin is a bird." (read as an
  existential, so Pingu is not known to be a bird; design, DECISIONS.md).
- "Kay" reads as "okay" (the grammar's word) and is refused UNKNOWN_WORD. Use another name.
- A name one edit from an accepted word is refused POSSIBLE_TYPO once, even when meant (the design; resend it).
- Words the grammar has as names only ("tove") can be refused rather than learned.

## Coverage of the grammar's own test items
- The ERG's gold test items are in the delph-in/erg repository (`tsdb/gold/*/item.gz`, about 45,000 sentences in the profiles fetched).
  `scripts/grammar_coverage.py` measures tolk on them. 200 random items: 2 compile (1.0%). See DECISIONS.md "Grammar coverage" and benchmarks/erg_items_sample200.json.
- A full run over all items takes hours at the measured speed; it is not in the suite.
- The predicate inventory of the grammar is not measured: the grammar's own predicate list is not in the repository.

## Testing gaps
- The 511-sentence mutation fuzz (open-items pass) is not a committed test.
- Nothing has verified the modals, control, proofs and persistence items independently; they have the suite and the clean-clone check.

## Parser and grammar
- ACE 0.9.34 and ERG 2018 only, Linux x86-64 (scripts/setup_erg.sh).
- Tagged input is a hint: an unknown word the tagged parse does not analyse falls back to the untagged parse.

## Continuous integration
- Actions: checkout v7, setup-python v7, cache v6 (Node 24). Runs on the local runner.
- The erg cache is restored but not saved on a hit; a miss downloads from sweaglesw.org.

## SQUID
- The legacy pipeline was removed from SQUID's `main` (`70cb408`), after the audit showed that only its two error classes were used. This overrides SPEC2's "leave the legacy module in place", on the owner's instruction. Its history is in git.
- Spider development set: 0 of 1034 questions produced SQL (benchmarks/spider_dev_2026-11-15.txt). A scope result; nothing was tuned.
- Values are read from the database only when the schema comes from SQLite.
- SQUID is pinned to v0.1.3. SQUID depends on tolk by git address; the tolk repository is private, so only its owner can install SQUID.

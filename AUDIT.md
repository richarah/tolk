# AUDIT

Audit of commit 3c3313d (SPEC2 phases 9 to 21), done by a session that did not build it. No code was changed to produce this file. `SPEC2.md` was not in the repository or its history; it was supplied by the user and copied in unchanged, and is committed with this file.

## 1. Full suite from a clean clone

`git clone` of the working tree to a scratch directory, `uv venv`, `uv pip install -e '.[test]'`, `.venv/bin/pytest -q`. One deviation from a pure clean setup: `erg/ace` and `erg/erg-2018.dat` were copied from the working tree instead of running `scripts/setup_erg.sh` (same files, no second 283 MB download).

```
........................................................................ [ 14%]
....................................................................x... [ 28%]
........................................................................ [ 43%]
........................................................................ [ 57%]
........................................................................ [ 72%]
........................................................................ [ 86%]
...................................................................      [100%]
498 passed, 1 xfailed in 21.06s
```

This equals the last PROGRESS.md entry (`498 passed, 1 xfailed`).

## 2. Changed assertions since the review commit (65ce12a)

Method: `git diff 65ce12a HEAD -- tests/*.py`, every removed or altered line. New test files and added tests are not listed; they change no earlier value.

| # | Test and change | SPEC2 sentence that authorises it | Verdict |
|---|---|---|---|
| 1 | `test_compile.EXPECTED["Birds are animals."]`: `rule ...` to `default ...` | Phase 18: "This changes "Birds are animals." in tier A from strict to default. Its dialogue results do not change." | authorised |
| 2 | `test_negation`: "Dogs do not bark." printed `rule` to `default` | Phase 18: "A bare plural generic ("Birds fly.", "Penguins do not fly.") is a default rule" | authorised |
| 3 | `test_dialogue_b`: "Every penguin is a bird." outcome was `== "rule stored"`, now first line is `rule stored` and the text must contain `conflict: fly(pingu) against not fly(pingu)` | Phase 19: "With it off, nothing is retracted and the conflict is reported with its candidates." Line 17 forbids changing a dialogue result "unless this file says so"; phase 19 says the report is added, the store result is unchanged | authorised, weakly (the tier B table itself says "stored") |
| 4 | `test_dialogue_b`: `UNSTRATIFIED` to `NEGATION_CYCLE` | Phase 9.6: "refused when the rule is told, with `NEGATION_CYCLE`" | authorised |
| 5 | `test_fixtures`: `test_every_sentence_has_a_reading` gained an xfail for "Every blorp flibbers." | None in SPEC2; SPEC.md phase 0 permits expected failure for a sentence with no reading. The task allows exactly this one | permitted |
| 6 | `test_generalise.REFUSED`: removed "Ada keeps two cats." | Phase 14: "A cardinal on an indefinite in a statement creates that many distinct anonymous things." | authorised |
| 7 | `test_generalise.REFUSED`: removed "Rio hums and Ada sings." | Phase 15 opens "The review made every conjunction a refusal. This phase replaces that." The listed cases are names, noun phrases and verb phrases; a clause-and is not named | authorised by the first sentence only; see F9 |
| 8 | `test_negation`: `test_wanted_variable_in_no_atom_is_refused` input "Who is Kim?" replaced by "Who is who?" and the `IDENTITY_NOT_YET` alternative dropped | Phase 10: ""Who is X?" and "What is X?" with a known name return a new logical form, `Describe(entity)`" | authorised |
| 9 | `test_negation`: `test_compile_refuses_an_unconstrained_wanted_variable` fixture "Who is Kim?" to "Who is who?" | same | authorised |
| 10 | `test_negation`: `test_negated_question_is_refused_not_answered_from_absence` replaced by `test_a_negated_question_is_not_answered_from_absence`; refusal `NEGATED_QUESTION` to `Unknown` | Phase 12: "negated questions, which are currently refused: "Does Kim not like Nemo?" is the plain question with the answer inverted ... Absence of a fact is still `Unknown`." Phase 18 for the bare-noun case | authorised |
| 11 | `test_review`: "Which dog does not bark?" `NEGATED_QUESTION` refusal to printed `ask X ...` | Phase 12 (same sentence) | authorised |
| 12 | `test_review`: "Kim sings and dances." refusal and zero facts to two stored predicates | Phase 15: "'And' between names, noun phrases and verb phrases distributes" | authorised |
| 13 | `test_review`: "Is every dog a mammal?" `UNIVERSAL_QUESTION` refusal to `Unknown` | Phase 18: ""Is every robin a bird?" is currently refused. Answer it ..." and "Known instances are never used as evidence" | authorised |
| 14 | `test_widening`: `test_numbers_are_refused` to a test that "Ana owns two cats." stores two things and "Every bike has three wheels." is refused | Phase 14: "A cardinal on an indefinite in a statement creates that many distinct anonymous things." The rule half is not in SPEC2; it stays refused, so no earlier value was loosened | authorised |
| 15 | `test_compile.FUNCTION_LEMMAS` gained `"i"`: the hard-rule-3 lemma scan now ignores the word "I" | **None.** Phase 13 makes "I" and "me" the entity `user` but says nothing about the scan | **finding F5** |
| 16 | `test_negation`: **deleted** `test_an_auxiliary_is_not_a_swallowed_word` (asserted the printed form `tell not _like_v_1(_, kim, sandy)`) | **None.** `test_choice.py:44` keeps only `chosen("Kim does not like Sandy.") == 1`, a weaker check of the same sentence | **finding F4** |
| 17 | `test_negation`: **deleted** `test_a_bare_plural_read_as_a_name_gives_no_empty_rule` (asserted the printed form, and that reading 1 compiles to `EMPTY_RULE_BODY`) | **None.** The printed form would now say `default` (authorised, item 2); the `EMPTY_RULE_BODY` assertion has no replacement. `test_choice.py:25` checks only the chosen index | **finding F4** |

Assertions that still hold but contradict SPEC2: `test_generalise.REFUSED` still lists "If Rio hums, Pip hums." as a sentence that must be refused. Phase 11 says it is a ground rule. See F2.

## 3. Skips and expected failures

`grep -rn "skip\|xfail\|expectedFailure\|importorskip" tests/*.py` finds one use: `tests/test_fixtures.py:15`, strict xfail for "Every blorp flibbers." Nothing else. The word `skipped` in two test names in `test_choice.py` is prose, not a skip. Clean.

## 4. Dialogues rerun through the repl, against SPEC2's tables

Each dialogue was run by hand through `scripts/repl.py` (phase 18 `policy=()` through `Mind(policy=())`), and the outputs read line by line.

| Phase | Result against SPEC2 |
|---|---|
| 9 | No dialogue table. Checked: "Kim can sing." refuses naming `_can_v_modal`; "Kim owns a dog." twice gives `already told` and one dog; "Who is who?" is `UNCONSTRAINED_WANTED`. Matches |
| 10 | "Who is Kim?" lists told facts with their sources; unknown name is `Unknown`. Matches |
| 11 | All three sentences store rules, and each fires from its antecedent. Matches. **But** "If Rio hums, Pip hums." is refused (F2) |
| 12 | The four lines of the dialogue: No with proof, Unknown, Yes, Unknown. Matches |
| 13 | "I am a person." / "Am I a person?" Yes ("you are a person") / "Are you a cat?" Unknown / "Tweety is a robin. It sings." stores `sing(tweety)` with `it = tweety` / "Kim likes Sandy. She is happy." refused `AMBIGUOUS_PRONOUN`. Matches |
| 14 | 2, Yes, Unknown, then 3 after "Kim owns a cat." Matches |
| 15 | "Kim and Sandy are happy." stores two facts; "or" in a statement refused; "or" in a question Yes from either side. Matches. "Is Lee happy or Kim happy?" (elided) is refused `UNCONSUMED`, while the unelided form works; noted under F10 |
| 16 | **Does not meet SPEC2's acceptance.** "Tweety is a blorp." stored, "Tweety is glorpy." stored, "Every blorp flibbers." refused (no reading), "Tweety flibbers." refused `UNKNOWN_WORD`, "Does Tweety flibber?" refused `UNKNOWN_WORD`. SPEC2: "`Yes`, or all four are refused with `UNKNOWN_WORD`." Neither holds: two stored, the others refused for two different codes. DECISIONS.md admits this. See F3 |
| 17 | `read("Rio sings.")` Tell; `read("Does Rio sing?", {"_sing_v_1"})` Ask; `read("Is the robin happy?")` `Refusal DEFINITE_NEEDS_STORE`. Matches; `__all__` checked by `test_phase17` |
| 18 | The five-row table: Yes; No by `specific` defeating "Birds fly."; with `policy=()` Conflict; "Tweety does not fly." stored; then No. Matches. Scale test passes in the suite |
| 19 | `diagnose()` lists the four sentences weakest first; "Forget that every bird flies." then Pingu No, Tweety Unknown. Matches |
| 20 | Yes (Kim before Lee), No (Lee before Kim), Oslo (2019), `Unknown` for "Does Sandy arrive?" after "Sandy arrived.". "Does Kim live in Oslo?" Unknown, "Did Kim live in Oslo?" Yes. Matches |
| 21 | Unknown, Yes, Unknown, plus "Who believes" Kim and "What does Kim believe?" `[swim(tweety)]`. Matches |

## 5. Own-word cases: expected results worked out first

I wrote 36 expectations from SPEC2 alone, three per phase, before running any of them (script in the session scratchpad, not in the repository). 33 matched at once. Three failed, and all three were my errors (two from one setup mistake), each rewritten and rerun with the expectation fixed in advance:

- Phase 19, "Tom is a cat. Every cat purrs. Tom does not purr." I told the negative after the rule. SPEC2 phase 18 refuses a told fact that contradicts a level 1 or 2 fact, so the refusal is right and my expectation was wrong. With the negative told first: forget the rule gives No; telling the rule again gives Conflict. Both as expected.
- Phase 19, "Forget that Tom is a cat." where I had never told it: `nothing that was told means that` is right.

Cases per phase (three each): 9 (modal refusal, repeat, `Who is who?`), 10 (Rio and Ada descriptions, unknown name), 11 (ground-name conditional, "If Rio hums, Ada is calm.", "If Ada owns a cat, Ada is happy."), 12 (negated question over a negative rule, negated question with no facts), 13 (it, he ambiguous, "I like Ada." then "Who likes Ada?" gives "you"), 14 (digits, "five" Unknown not No, bare plural subject), 15 (verb-phrase and, or in question, `Do Kim and Sandy sing?` Unknown), 16 (noun, adjective, verb), 18 (identical-body defaults give Conflict, strict Yes without "default", "Yes, by default"), 19, 20 (year order both ways, derived past event), 21 (holder, verb must match).

## 6. Code checks for phases 18 to 21

- **18, `specific` is decided by deriving.** `defaults.implies` builds the goal from rule b's body and calls `entails`, which calls `scratch` (a fresh store holding only the strict rules, a's body asserted about fresh things), runs the engine, and looks for a match. It compares no names or text. The one comparison, `if a == b` in `_separate`, is on rule ids. Confirmed.
- **18, `policy=()` gives Conflict.** `_separate` returns `None` with no criteria, `_decide` skips the pair, both facts stay and the conflict is recorded. Shown above: `Does Pingu fly?` is Conflict. Confirmed.
- **18, the blocked loop ends.** `rebuild` repeats while `_decide` returns true; it returns true only when `INSERT OR IGNORE INTO defeat` adds a row, and `defeat` is cleared once before the loop and never inside it. A finite set of instances, so it ends. Confirmed by reading; no test constructs a case with more than two passes.
- **18, the scale test.** `tests/test_engine.py` is unchanged (additions only) and passes: 300,000 derived facts.
- **19, an observation is never a candidate.** `Mind._candidate` skips any sentence with `observation` set. Shown: after `observe("Tweety does not fly.")`, `diagnose` lists only the three other sentences. Confirmed.
- **19, retract rebuilds the cache.** `_retract` calls `store.retract` then `defaults.rebuild`. Shown: after `retract`, "Does Tweety fly?" is No, with the derived level 2 and 3 facts regenerated. Confirmed.
- **20, axioms are named in proofs.** Proof of the year case: `before(e1, e2)  (by built-in axiom: an event in an earlier year is before an event in a later year)`; transitivity and asymmetry likewise. Confirmed.
- **21, nothing is derived in a claim, and the world is unchanged.** With "Every robin is a bird." and "Every bird flies." in the store, "Kim believes that Tweety is a robin." leaves exactly two fact rows: the world fact `_believe_v_1(e1, kim, claim1)` and `_robin_n_1(tweety)` in context `claim1`. No `_bird_n_1`, no `_fly_v_1` anywhere; "Is Tweety a bird?" and "Does Tweety fly?" are Unknown. Confirmed.

## 7. Hard rules

- **Rule 3, content words in `tolk/`.** The scan in `test_compile.py` passes, but is weak (F5). My own scan over every lemma in all 162 fixtures, comments and docstrings excluded, finds only function words and ordinary Python names, with these exceptions: the regex `forget that` in `mind.py:22` (Mind's own command, in DECISIONS.md); `_if_x_then`, `_(before|after)_x_h` and the `before`/`after`/`if` branches in `compile.py`, `conditional.py` and `temporal.py`. Those are function words, but SPEC.md rule 3 allows keys only on a quantifier name, an abstract predicate, a part of speech or an argument pattern. A judgement call, recorded as F5.
- **Rule 9, modules over 300 lines.** `wc -l tolk/*.py`: `mind.py` 347, `store.py` 319, `compile.py` 312. **Three violations (F6).** PROGRESS.md's checkpoint said `compile.py` was 256.
- **One fact, two homes.** The join that finds a fact and its opposite is written three times: `defaults.py:13` (`CLASH`), `engine.py:77` and `store.py:216` (F7). The unknown-word shape has two regexes, but they match two different things (the grammar's output and the store's form), so that is not a duplicate.
- **SQL built from values.** Every f-string in `execute` interpolates generated aliases, fixed column names or fixed constants (`lf.BEFORE`, `lf.TENSE`); values go through `?`. `defaults.py:122` interpolates `column`, which is one of two literals chosen by an `if`. No violation.
- **Swallowed errors.** `engine.py:97` catches `ValueError` from `strata` and acts on it (a refusal). `scripts/repl.py:20` catches `Exception`, prints one line and the full traceback to stderr, as SPEC2 phase 9 requires. No violation.

## Findings

Severity first. A finding has a fix in Part 2 unless stated.

- **F1. SPEC2.md was never committed.** Documents cite it and tests quote it (`test_phase14.py`, `test_phase19.py`), but the file did not exist. Fixed by committing it.
- **F2. A wrong refusal that a test encodes.** "If Rio hums, Pip hums." is refused `UNCONSUMED: no atom uses x11` on an empty store, while "If Rio hums, Lee hums.", "If Tom hums, Pip hums." and "If Rio hums, Kim hums." all store ground rules. Phase 11 says a ground rule is allowed. The cause is a reading choice, and falls under Part 2A. `test_generalise.REFUSED` lists the sentence as refused, which SPEC2 phase 11 contradicts; the entry is removed when the choice is fixed (phase 11 authorises it).
- **F3. Phase 16 acceptance is not met as written.** Neither "Does Tweety flibber?" is Yes nor all four refused with `UNKNOWN_WORD`. "Tweety flibbers." itself is refused. Part 2B.
- **F4. Two tests were deleted with no authorising sentence** (rows 16 and 17 above). Restored in Part 2, the `Fish do not fly.` one with `default` in the printed form, which phase 18 authorises.
- **F5. The rule-3 scan was loosened and is weak.** `"i"` added to its exemptions (row 15); it reads comments (twelve comments reworded for it, per PROGRESS.md); it covers only `sentences.txt` lemmas, so words from `own.txt`, `generalise.txt` and the others are never scanned; it ignores abstract part-of-speech `x` and `q` predicates. The `if`/`before`/`after` keys are a judgement call. Part 2C makes the scan ignore comments; the "i" exemption stays because the grammar carries "I" as an argument of `card` and removing it would fail the scan on a function word, but it is a loosening and is reported here.
- **F6. Three modules are over 300 lines** (`mind.py`, `store.py`, `compile.py`). Part 2C, to 250.
- **F7. One fact with three homes:** the fact-and-opposite join. Fixed in Part 2.
- **F8. Narrow refusal codes added to steer the reading choice.** The three are `FALLBACK_PARSE` (phase 11), `GRAMMAR_ARTIFACT` (phase 20) and `DEMONSTRATIVE` (phase 21), each a reading refusal that makes the choice skip one reading. DECISIONS.md records that phase 20's and phase 21's were each added because a wrong reading ended the search. This is the pattern Part 2A replaces.
- **F9. Clause-and.** Phase 15's list names names, noun phrases and verb phrases. "Rio hums and Ada sings." (two clauses) was moved from refused to stored on the strength of the section's first sentence. A reading of SPEC2, not a violation; noted.
- **F10. "Is Lee happy or Kim happy?"** is refused `UNCONSUMED`, while "Is Lee happy or is Kim happy?" and "Is Kim happy or sad?" are answered. A grammar elision shape not handled. Not fixed; no SPEC2 sentence requires it.
- **F11. Phase 16 stores a pseudo-predicate shape and widens by part of speech.** DECISIONS.md documents it. Part 2B tests whether the parser can take part-of-speech tags instead.

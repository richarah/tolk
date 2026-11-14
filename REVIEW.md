# REVIEW

Reviewed from a clean clone at commit 281dbe2 (after fixes A and B), then fixed. All numbers below were pasted from the commands named.

## State

Clean checkout: `git clone`, `sh scripts/setup_erg.sh` (ACE 0.9.34, erg-2018.dat 283401864 bytes), `uv venv .venv && uv pip install -e '.[test]'`, `.venv/bin/pytest -q` gave `181 passed in 7.47s`. Re-recording every sentence file with `scripts/record.py --force` into that clone left `git status` clean: fixtures are byte-identical to what the script produces. No orphan or missing fixtures.

| Phase | Acceptance | Result |
|---|---|---|
| 0 | fixtures for every sentence; three readings in PROGRESS.md | passing |
| 1 | tier A printed forms; lemma scan | passing |
| 2 | derived facts; idempotent tell; one owner; recursion stops; 50,000 facts | passing (300000 derived facts in 1.91s) |
| 3 | tier A dialogue; proofs with told leaves; repl prints reading, form, result | passing (run by hand through the repl) |
| 4 | tier B dialogue | passing (run by hand) |
| 5 | tier C dialogue | passing (run by hand) |
| 6 | suppose, conflict inside only, drop | passing, but drop did not restore the exact state (finding 8) |
| 7 | coverage script, refusals by code | passing |
| 8 | one proposal with four things; none with a counterexample | passing |

Hard rules checked: no content lemma in `tolk/` (scan of all `tolk/**/*.py` against `sentences.txt` finds only function words); no `try`/`except` anywhere; no SQL value is interpolated (the f-strings in `engine.py`, `ask.py`, `store.py` insert generated aliases and `?` placeholders only); no module over 300 lines (largest: compile.py, see `wc -l tolk/*.py`); no skipped or expected-failure tests. No violation found.

## Findings

Numbered by severity. Status is after the fixes.

1. **Wrong result.** A negated indefinite or bare noun stored a thing that exists: "Kim does not like fish." gave `not like(_, kim, a1)`, `fish(a1)`. Cause: the subject of a negated sentence was not seen as the main clause's subject, and an object under `neg` was treated as a fresh existential. Reading 1 was also the verb "to fish" with "like" swallowed. Fixed (DECISIONS.md: a negated indefinite is a negative rule; a span-vote tie-break prefers the reading that swallows fewer words).
2. **Wrong result.** "Dogs do not bark." stored one dog and lost the universal (same cause as 1). Fixed.
3. **Wrong result.** A refused top reading was overridden by a worse lower one: "Nobody flies." stored a fact about a thing named `nobody`; "Which dog does not bark?" was answered from a reading where `dog` is a verb. Fixed: a refusal for an unrepresentable meaning ends the search; malformed readings are skipped. This changes the spec's "among those that are not refusals" (see Spec problems).
4. **Wrong result.** "or" was stored as "and": "Every dog barks or sleeps." gave `bark(E!, X), or_c(E, E1!), sleep(E1, X) :- dog(X)`, which derives both. "Kim sings and dances." stored a fact joining two events that exist nowhere else. Fixed: conjunctions are refused `COORDINATION`.
5. **Wrong result.** Future, perfect and progressive were dropped: "Kim will sing." stored `sing(kim)`, and a relative clause in the past ("who owned a dog") applied to present owners. Fixed: refused `UNSUPPORTED_TENSE` / `UNSUPPORTED_ASPECT`.
6. **Wrong result.** "Is every dog a mammal?" was answered as "is some dog a mammal". Fixed: refused `UNIVERSAL_QUESTION`.
7. **Wrong result.** A negated question ("Does Kim not like fish?") answered Yes from the absence of a fact (negation as failure in the question), and "Does Kim not like Nemo?" crashed the repl. Fixed: refused `NEGATED_QUESTION`.
8. **Wrong result.** `Who is Kim?` crashed with a KeyError (finding B). A rule with an empty body (the name reading of "Fish do not fly.") crashed the engine. Fixed: `UNCONSTRAINED_WANTED`, `EMPTY_RULE_BODY`, both from compile. No sentence tried in this session now exits the repl.
9. **Rule violation.** A merge could leave a `why` row naming a premise fact that was deleted as a twin (`prove` would then fail on that row). Fixed: premises are rewritten to the twin.
10. **Rule violation.** Dropping a supposition left its sentence row behind and changed the rules' `ran` round, so the state was not exactly restored (SPEC phase 6 says it is). Fixed; the test compares every table.
11. **Fragile.** The check that "every predication is consumed" was not a check: a predication no family handles is refused, but a `neg` that negated nothing, or a quantified variable that no atom used, passed silently. Fixed with `_unconsumed`.
12. **Fragile, unresolved.** Preposition senses (`_in_p_loc` against `_in_p_state`) and verb senses (`work_v_1` against `work_v_in`) differ between the statement and the question when the parser ranks them differently, so a told fact may not answer its own question. Overlap with the store cannot repair it, because it counts predicates, not senses. Not fixable without a sense-merging rule that this spec does not allow.
13. **Fragile, unresolved.** Negation as failure is evaluated per round, not per stratum (DECISIONS.md already says so). A negated body atom whose predicate is derived late can fire early.
14. **Fragile, unresolved.** A repeated statement is detected by its text, not its meaning; a definite description ("The robin sings.") told twice in a changed world is not stored again. Not tested here.
15. **Untidy, unresolved.** Modals and control verbs ("Rio might swim.", "Ada wants to sleep.") are refused `UNBOUND_VARIABLE h9`, which is correct and unhelpful. The refusal is safe; its detail is not.
16. **Untidy.** The README and PROGRESS.md say the suite has 80 tests; PROGRESS.md was not rewritten here. Do not rely on its counts.

## Generalisation

Three dialogues with the tiers' constructions and different words, and ten sentences that should be refused: `tests/test_generalise.py` (50 steps), fixtures in `tests/fixtures` from `scripts/record.py` over `tests/generalise.txt`. Before the fixes above, these steps exposed findings 3, 4 and 5 (the "or" rule, the tense drop, and the name readings); the tier rules themselves, with new words, were correct. "kiwi" and "emu" are unknown to the grammar and were replaced by "puffin".

Result with the final code: 50 steps, 0 wrong.

| Sentence | Expected | Actual | |
|---|---|---|---|
| Rio is a sparrow. | stored | stored, 1 new fact(s) | ok |
| Every sparrow is a finch. | rule stored | rule stored | ok |
| Every finch swims. | rule stored | rule stored | ok |
| Finches are creatures. | rule stored | rule stored | ok |
| Rio hums. | stored | stored, 1 new fact(s) | ok |
| Every sparrow that hums is cheerful. | rule stored | rule stored | ok |
| Ada is a teacher. | stored | stored, 1 new fact(s) | ok |
| Ada keeps a cat. | stored | stored, 2 new fact(s) | ok |
| Every teacher who keeps a cat is calm. | rule stored | rule stored | ok |
| Ada admires Bo. | stored | stored, 1 new fact(s) | ok |
| Tom is a cat. | stored | stored, 1 new fact(s) | ok |
| Every cat has a master. | rule stored | rule stored | ok |
| Does Rio swim? | Yes | Yes | ok |
| Is Rio a creature? | Yes | Yes | ok |
| Is Rio cheerful? | Yes | Yes | ok |
| What swims? | Rio | Rio | ok |
| Which sparrow hums? | Rio | Rio | ok |
| Who is calm? | Ada | Ada | ok |
| Who admires Bo? | Ada | Ada | ok |
| Who does Ada admire? | Bo | Bo | ok |
| Is Bo calm? | Unknown | Unknown | ok |
| Does Tom have a master? | Yes | Yes | ok |
| Pip is a puffin. | stored | stored, 1 new fact(s) | ok |
| Pip does not swim. | stored | stored, 1 new fact(s) | ok |
| Does Pip swim? | No | No | ok |
| No puffin swims. | rule stored | rule stored | ok |
| Every puffin is a finch. | rule stored | rule stored | ok |
| Does Pip swim? | Conflict | Conflict | ok |
| Bruce Wayne is Batman. | one thing | one thing: bruce_wayne and batman | ok |
| Batman swims. | stored | stored, 1 new fact(s) | ok |
| Does Bruce Wayne swim? | Yes | Yes | ok |
| Is the sparrow cheerful? | Yes | Yes | ok |
| The cat purrs. | refused | refused | ok |
| Rio does not swim. | refused | refused, contradicts: | ok |
| Ann sleeps in Rome. | stored | stored, 2 new fact(s) | ok |
| Bob departed. | stored | stored, 2 new fact(s) | ok |
| Who sleeps in Rome? | Ann | Ann | ok |
| Where does Ann sleep? | Rome | Rome | ok |
| Does Ann sleep in Rome? | Yes | Yes | ok |
| Does Ann sleep in Paris? | Unknown | Unknown | ok |
| Most cats purr. | refused | refused | ok |
| She swims. | refused | refused | ok |
| Rio might swim. | refused | refused | ok |
| Rio is smaller than Pip. | refused | refused | ok |
| Ada keeps two cats. | refused | refused | ok |
| If Rio hums, Pip hums. | refused | refused | ok |
| Rio hums and Ada sings. | refused | refused | ok |
| Sing! | refused | refused | ok |
| Ada wants to sleep. | refused | refused | ok |
| Every finch that swims quickly is cheerful or calm. | refused | refused | ok |

The free-form sentences from the manual-use session (negation, questions, bare nouns) are in `tests/negation.txt` and `tests/generalise.txt`; their fixtures are recorded.

## Spec problems

- "Choosing a reading" says to pick among readings that are not refusals. That is how a refused reading is replaced by a nonsense one (finding 3). It also leaves ties to the parser's order, which can be a reading that swallows a word (finding 1). Both needed rules the spec does not give.
- The spec does not say what a negated indefinite means, what to do with tense other than past, or what a universal or negated question is. All three were answered by silent wrong behaviour, and are now in DECISIONS.md.
- Rule 3 forbids content words, but the lemma scan reads only `sentences.txt`, so a lemma from another file passes it.
- "Absence of a fact is Unknown" and negation as failure in rule bodies are both required, with nothing to say a question must not use the second.
- The tier A dialogue lists "Is Sandy happy? Unknown" but gives no case where a question has a wanted variable that nothing constrains (finding 8).

## Unresolved, and final output

Findings 12, 13, 14 and 15 are unresolved (reasons given with each).

Final test output: `204 passed in 8.76s`.

Coverage, `scripts/coverage.py tests/sentences.txt tests/extra.txt tests/round1.txt tests/round2.txt`:

```
compiled 71 of 86 (82.6%)
  11  DEFINITE_MATCHES  0 known things match
   4  UNSUPPORTED_PREDICATE  card
```

# tolk status

tolk reads English with ACE and the English Resource Grammar, keeps what it is told with its source in SQLite, reasons over it, and answers
with proofs. Numbers below come from `scripts/status.py`, `scripts/coverage.py` and `scripts/word_table.py`; nothing else is quoted.

## What it can do (each line: told, then asked, with what comes back)
| Capability | Example |
|---|---|
| Facts, rules, proofs | "Every bird is an animal." "Tweety is a bird." "Is Tweety an animal?" → Yes, `tweety is an animal (by rule 1)` |
| Defaults and defeat | "Birds fly." "Penguins do not fly." "Tweety is a penguin." "Does Tweety fly?" → No (the specific rule wins) |
| Clause "and": two statements | "Kim sings and Sandy dances." → 2 new facts; "Forget that Kim sings." removes one |
| Conditionals | "If Kim sings, Sandy dances." "Kim sings." "Does Sandy dance?" → Yes |
| Comparatives | "Kim is taller than Sandy." "Sandy is taller than Lee." "Is Kim taller than Lee?" → Yes, by the built-in transitivity axiom |
| Time | "Kim arrived before Sandy left." "Did Kim arrive before Sandy left?" → Yes |
| Claims | "Kim believes that Tweety swims." "Does Kim believe that Tweety swims?" → Yes (not a fact about Tweety) |
| Unknown words | "Tweety is a blorp." "Tweety flibbers." "Does Tweety flibber?" → Yes (class from first use, given as tagged input) |
| Describing a kind | "I love Veronika." "What is love?" → `(widened: love (noun) matched as love (verb))`, `Known: 1: love(you, veronika)` |
| Revision | "Forget that Kim owns Rex." → forgot; the question is Unknown again |
| Wider search | "If Rio hums, Pip hums." → a rule (the right reading is the parser's sixth) |
| Spelling | after "Tweety is a robin.", "Twety sings." → refused POSSIBLE_TYPO suggesting tweety; sent again it is stored |
| Closed world | `Mind(closed_world=True)`: "Does Kim not own Fido?" → Yes when nothing says Kim owns Fido |

## Refusal codes
Every code is `final` (the sentence was understood or cannot be read; the search ends) or `reading` (this reading is unusable, the next is
tried). The table is `tolk/lf.py` REFUSALS; its contents are printed by `scripts/status.py`.

| Code | Kind | Triggered by |
|---|---|---|
| AMBIGUOUS_PRONOUN | final | a pronoun with two agreeing antecedents |
| ARGUMENT_GAP | reading | a predicate with a gap among its arguments |
| CONTRADICTS | final | a statement whose opposite is stored |
| COORDINATION | final | or in a statement; and with or in one list; a group in a rule |
| DEFINITE_MATCHES | final | "The dog barks." when none or several known things match |
| DEFINITE_NEEDS_STORE | final | a definite read without a store |
| DEMONSTRATIVE | reading | "that" read as a demonstrative |
| EMPTY_RULE_BODY | reading | a rule whose restriction has no atom |
| FALLBACK_PARSE | reading | a word the grammar did not analyse |
| GRAMMAR_ARTIFACT | reading | the grammar's bookkeeping predicates (subord, place_n, ...) |
| IDENTITY_NOT_YET | final | "Every robin is Tweety." |
| NEGATED_INDEFINITE | final | a negated clause in a rule body that introduces a thing |
| NEGATION_CYCLE | final | a rule set with a cycle through negation |
| NO_ANTECEDENT | final | a pronoun with nothing agreeing mentioned |
| NO_EVENT_READING | final | no reading has a predicate on the sentence event |
| POSSIBLE_TYPO | final | a new name or unknown word one edit from exactly one known word |
| SCOPE_AMBIGUOUS | final | "every" under negation |
| TOO_MANY_ARGUMENTS | reading | a predicate with more than three arguments |
| UNBOUND_VARIABLE | reading | a variable that nothing binds |
| UNCONSTRAINED_WANTED | reading | a wanted variable with no restriction |
| UNCONSUMED | reading | a negation, question or rule with nothing for it to apply to |
| UNEXPRESSED_OBJECT | reading | an object the sentence leaves out |
| UNEXPRESSED_SUBJECT | reading | a subject the sentence leaves out |
| UNIVERSAL_QUESTION | final | a question over every thing |
| UNKNOWN_WORD | final | a word the grammar lacks, in a class the store cannot hold (or a small-letter name) |
| UNSAFE_NEGATION | final | a rule whose body has nothing positive |
| UNSUPPORTED_ASPECT | final | progressive or perfect |
| UNSUPPORTED_FORCE | final | an imperative or other sentence that is neither statement nor question |
| UNSUPPORTED_PREDICATE | final | a predicate with no form in the store ("more than", "want", measure, ...) |
| UNSUPPORTED_QUANTIFIER | final | "most", "half" and the like |
| UNSUPPORTED_TENSE | final | a tense the store does not hold (future, past inside a rule) |
| WH_BOUND_TO_CONSTANT | reading | a wh word fixed to a name |

## Settings
| Setting | Values | Default | Where |
|---|---|---|---|
| `policy` | specific, trusted, recent (a list) | specific | `Mind(policy=...)`, meta |
| `auto_revise` | on, off | off | `Mind(auto_revise=...)`, meta |
| `closed_world` | on, off | off | `Mind(closed_world=...)`, meta |
| `wording` | template, generated | template | `Mind(wording=...)`, meta |
| `TOLK_ERG_DIR` | a directory | `erg/` of the checkout | environment, read at import |
| repl: `TOLK_POLICY`, `TOLK_AUTO_REVISE`, `TOLK_CLOSED_WORLD`, `TOLK_WORDING` | as above | as above | `scripts/repl.py` only |

## Known limits
- The parser returns 5 readings, 25 on a second try; a right reading beyond 25 is not found.
- Proofs use template wording unless `wording="generated"`, and then only for facts the grammar says back exactly.
- A name the grammar has as a word ("Kay" is `okay`) can be refused; a word the grammar has only as a name ("tove") is refused UNKNOWN_WORD.
- Three narrow reading refusals (FALLBACK_PARSE, GRAMMAR_ARTIFACT, DEMONSTRATIVE) each decide a row of `tests/choice_table.json`.
- The closed world leaves "Is every X a Y?" alone, and a wh question with no support answers "Nothing".
- A typo that is itself a word the grammar knows is not caught; a deliberately new name one edit from a known one is refused once.
- The reading choice was checked only against the stores the suite builds.

## Open items from VERIFY.md
(see the end of this file once the verification rounds are in)

## Open items from VERIFY.md (after two rounds, and after the release session)
Round 1 found 11 mismatches: 5 fixed (Where is Bob?, underscored word, preposition "if", group subject with a noun complement, `_not_c` stored in a rule), 1 not a defect, 1 confounded (SQUID), 4 open. Round 2 found 4, not fixed by instruction. The release session fixed or decided the following:
- Identical extensions of two predicates now give one proposal (in one direction, none once a rule links them either way).
- "A blips sleeps." no longer raises: `reading.read` returned the readings it had set aside with a choice made among others. `tests/test_error_class.py` and a fuzz of 511 sentences with four mutations each found no other exception.
- "Is Kim happy or Lee happy?" is a question of two alternatives (the auxiliary is written out for the grammar when the sentence is refused otherwise). "Or" in a statement stays refused.
- The wider search runs only when no first reading was usable: a final refusal ends the search.
- "Do all penguins fly?" answering "No, by default" is intended (DECISIONS.md).
- SQUID: a value in a row is read as that value (the SQUID repo, `squid/values.py`).

Still open:
1. "Tweety is a blips." (ungrammatical) is refused NO_EVENT_READING, not UNKNOWN_WORD; "Blips are things." is refused EMPTY_RULE_BODY.
2. "Ola owns more than two cellos." is refused UNKNOWN_WORD, not more_comp.
3. "Quorl is a thing." stores the invented word as a name (arguable).
4. "Are Kim and Lee happy or is Sam happy?": the second alternative also asks whether Lee is happy, so a store that says only that Sam is happy answers Unknown, not Yes.
5. A past-tense question with an "or" is refused UNSUPPORTED_TENSE like any past-tense question.

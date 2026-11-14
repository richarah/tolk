# PLAN.md: tolk, phases 0 to 8

Revised after reading every first reading in tests/fixtures (phase 0 step 6).
Statements about parser output below were checked against those fixtures.

## Standing rules (from the user, mid-session)

- One home per fact. Schemas, constant sets, id formats and concept definitions
  are written once and imported. Example: the slug and sentence list live in
  `tests/helpers.py` only.
- Similar-looking code may appear twice. On the third occurrence, factor it into
  one function and delete the copies.
- No indirection for one use. No base class, registry or wrapper with one
  implementation or one caller.
- Mapping rules share one shape from phase 1. Each family module in
  `tolk/rules/` exposes `map_ep(ctx, ep) -> Mapped | Refusal | None`. It returns
  `None` for predicates it does not own. `compile.py` calls the families in a fixed
  order with an if-chain, not a dict registry. `ctx` carries the reading, the
  variable classes and the lookup. `Mapped` is the list of atoms plus any rule or
  tell fragment it adds.

## Spec problems and resolutions

1. One phase per session. Overridden by the user: continue when checks pass.
2. Phase 6 Conflict. The tier B dialogue never tells "No penguin flies.", so
   supposing "Tweety is a penguin." only adds a positive fly. Resolution: the
   phase 6 test tells "No penguin flies." in `world` after tier B, then supposes.
3. Conflict rows. Spec phase 4 says "derived and derived", but the tier B
   dialogue makes a conflict when the negative was told and the positive derived.
   Resolution: after each engine run, record a conflict for every positive/negative
   pair where at least one side is derived. Telling a fact whose opposite is stored
   is still refused.
4. One INSERT...SELECT per rule cannot cover multi-atom heads ("has an owner" is
   `_have_v_1` plus `_owner_n_of`). Resolution: one `INSERT OR IGNORE ... SELECT`
   per head atom, sharing one generated FROM/WHERE, then `why` and skolem `entity`.
5. Lemma scan. Literal "no lemma in source" also bans `in`, `is`, `not`. Resolution:
   the scan takes the content lemmas from fixture predicates (`_lemma_[nva]_N` and
   `_lemma_[nva]` forms, `_lemma_v_id` included), plus every CARG, matched whole-word
   case-insensitively after splitting on `_`. Predicates that are only function
   words (`_be_v_id`, `_a_q`, `_every_q`, `neg`) are not content and may be named.
6. `fact` has three argument columns. Atoms with more than three arguments (event
   plus three) are refused `TOO_MANY_ARGUMENTS`.
7. No pip on this machine. `uv venv .venv` and `uv pip install -e .[test]`.
   `uv` is an installer only, not a runtime dependency. Recorded in DECISIONS.md.
8. Definites ("Is the robin happy?") need store lookup, so `compile` takes an
   optional `lookup`. Phase 1 tests pass none.
9. Reading choice needs one structural pre-filter the spec does not give. Fixture
   facts: `Every bird flies` reading 0 has `_fly_n_1` on `x4` and its sentence index
   `e2` is bound only by `unknown`; reading 1 has `_fly_v_1(e2, x3)`. `Superman flies`
   reading 0 has an unknown-word predicate `_superman/jj_u_unknown`, reading 2 has
   `named(Superman)` with `_fly_v_1(e2, x3)`. Resolution: a reading is *eventive* if
   some EP has `ARG0` equal to the index and its predicate is not `unknown`. Only
   eventive, non-refused readings are candidates. Then overlap with the store, then
   parser order. Recorded in DECISIONS.md. Phases 1 and 4 tests check this.
10. Compound names. Fixture for "Clark Kent is Superman.": `compound(ARG1=x3 named
   "Kent", ARG2=x9 named "Clark")`. The head is ARG1 and comes last in the text.
   Constant id = ARG2 name + `_` + ARG1 name, lowercased: `clark_kent`.
11. Unknown-word predicates (names containing `/` and `unknown`) are refused as
   `UNKNOWN_WORD` if the reading is chosen. They are not guessed.

## Facts from the fixtures used below

- Force: `props[index]["SF"]` is `prop` or `ques`. Tense: `TENSE` is `pres` or
  `past`. Only `past` is stored (tense fact).
- Quantifiers: `_every_q`, `_a_q`, `_the_q`, `_no_q`, `udef_q` (bare plural),
  `proper_q` (names), `which_q` (wh-words). Restriction = EPs whose label is
  `qeq[RSTR]`. Example: `Every robin that sings is happy`: `qeq[h5]=h7`, and
  `_robin_n_1` and `_sing_v_1` both have label `h7`.
- Names: `named` with `CARG`, `ARG0` = the thing. Wh-questions: `which_q` with
  `RSTR` restricted by `person` ("Who"), `thing` ("What"), `place_n` ("Where"),
  or the noun in the question ("Which robin").
- Copula: `_be_v_id(e2, x_subject, x_complement)`, complement under `_a_q`/`udef_q`.
- Negation: `neg(e9, ARG1=h)`, where `qeq[h]` is the negated clause's label. Example
  `Pingu does not fly`: `neg ARG1=h10`, `qeq h10->h11`, `_fly_v_1(e2, x3)`.
- Unexpressed args: `i`-variables (`i9`, `i10`, `i14`) that no other EP uses.
  `Tweety sings`: `_sing_v_1(e2, x3, i9)`, so `i9` is dropped as trailing. An
  `x`-variable with no restriction is not an unexpressed argument.
- Owner nouns: `_owner_n_of(x8, i13)`, with the `i13` unexpressed and dropped.
- Locatives: `_in_p_loc(e9, e2, x10)` and `_in_p_state(e9, e2, x10)` both appear.
  "Kim lives in Oslo" reading 0 has `_in_p_loc`. Which one a question gets depends
  on the store overlap rule (item 9). `loc_nonsp(e4, e2, x5)` with `place_n(x5)`
  appears for "Where does Kim live?", reading 0.
- Past tense: "Sandy arrived." has `TENSE: past` on `e2`.
- "The dog barks." is `_the_q` plus `_dog_n_1` plus `_bark_v_1(e2, x3)`.

## Files, budgets, public signatures

| File | Lines | Public surface |
|---|---|---|
| `scripts/setup_erg.sh` | 25 | done |
| `tolk/erg.py` | 40 | done: `parse(text) -> list[str]`, `close()`. Uses `delphin.ace.ACEParser`, `-n 5`. |
| `tolk/sem.py` | 60 | done: `EP`, `Reading`, `read(simplemrs) -> Reading`, `to_dict(r)`. `qeq` keys are the handle `hi`, values `lo`. |
| `scripts/record.py` | 40 | done: fixtures from `tests/sentences.txt`, skips existing unless `--force` |
| `tolk/lf.py` | 110 | `Const, Var, Atom, Tell, Rule, Ask, Same, Refusal`; `show(lf) -> str` |
| `tolk/compile.py` | 200 | `compile_reading(r, lookup=None) -> LF`; `choose(readings, store_preds, lookup) -> (int, LF)`; applies item 9 |
| `tolk/rules/names.py` | <=120 | `named`, `compound`, unknown-word refusal |
| `tolk/rules/quant.py` | <=150 | restriction walk; `_every_q`, `_a_q`, `_the_q`, `_no_q`, `udef_q`, `which_q` |
| `tolk/rules/copula.py` | <=120 | `_be_v_id` |
| `tolk/rules/neg.py` | <=120 | `neg` (phase 4) |
| `tolk/rules/modifiers.py` | <=120 | `_in_p_*`, `loc_nonsp`, tense (phase 5) |
| `tolk/store.py` | 220 | `open_store(path)`, `tell`, `add_rule`, `merge`, `known_preds`, `match_definite`, `drop_ctx` |
| `tolk/engine.py` | 230 | `atom_sql(...)` shared FROM/WHERE generator (used by rules and asks); `rule_sql`; `check_stratified`; `run(db, ctx) -> int` |
| `tolk/ask.py` | 150 | `Answer(value, bindings, proofs)`, `Proof`, `answer(db, q, ctx)`, `prove(db, fact_id)` |
| `tolk/say.py` | 110 | `fact_text`, `proof_text`, `answer_text` |
| `tolk/mind.py` | 200 | `class Mind`: `tell`, `ask`, `hear`, `suppose`, `drop`, `propose`, `confirm` |
| `scripts/repl.py` | 40 | reads lines, prints `reading k of n`, printed LF, result |
| `scripts/coverage.py` | 60 | share compiled, refusals by code and predicate |

`Mind` is the only class with state. Everything else is functions.

## Steps

### Phase 0: done except commit
Checks run: `pytest -q` gives 80 passed. `setup_erg.sh` ran. Fixtures: 40, each with
1 to 5 readings. Revised PLAN.md above. PROGRESS.md must have the three full first
readings.

### Phase 1: logical form and core mapping (tier A)
1. `lf.py`, `show`; unit tests on hand-built LF objects.
2. `compile.py`. Force from `props[index].SF`. Walk quantifiers via `qeq[RSTR]`.
   Event atoms take the event as first argument. Trailing `i`-variables dropped.
   Gaps refused. Unknown preds refused `UNSUPPORTED_PREDICATE`.
3. `tests/test_compile.py`: expected-string table for all 23 tier A sentences.
   Lemma scan per resolution 5. Verify: `pytest -q tests/test_compile.py`.

### Phase 2: store and engine
Schema as the spec. Constant SQL strings, bound `?` params. Rule SQL: one generated
FROM/WHERE per rule, one `INSERT OR IGNORE ... SELECT` per head atom. Semi-naive by
`round`. Skolem id from rule id, variable name and bindings. Test: five acceptance
items; 50,000-fact timing pasted from `pytest -s`.

### Phase 3: questions, proofs, repl
`ask.py` reuses `engine.atom_sql`. `say.py` templates by predicate POS suffix
(`_n_`, `_v_`, `_a_`, `_p_`). Test: ten tier A dialogue rows, proof leaves are told
sentences, repl `subprocess` test on three inputs.

### Phase 4: negation, "no", identity, definites (tier B)
`neg` with `ARG1` handle resolved through `qeq`. Body negation `NOT EXISTS` with a
stratification check. `_no_q` restriction plus body/head negation.
Test: tier B rows in order, plus printed forms. Verify: full `pytest -q`.

### Phase 5: modifiers and time (tier C)
`_in_p_loc` atoms on the event. "Where" maps to a wanted variable on the locative
preposition, decided from the store-overlap rule (item 9) and the `loc_nonsp` fixture.
`tense(e, past)`. Test: five tier C rows, printed forms.

### Phase 6: suppositions
`Mind.suppose`, `Mind.drop`, ctx threading. Test per resolution 2. Fact count
before supposition equals count after drop.

### Phase 7: widening coverage
`tests/extra.txt`: about 40 everyday sentences written before any result is seen.
Up to five rounds of the spec's loop. Record fixtures, read them, DECISIONS.md,
rule, tests, coverage before and after.

### Phase 8: proposing rules
`Mind.propose()`: one-place predicates P and Q over known things in `world`, at least
three things with P, all with Q, no existing rule deriving Q from P. `Mind.confirm(p)`
stores the rule. Test: four things sharing two predicates gives one proposal; a
counterexample gives none; nothing stored before confirm.

### Final pass
Reread `tolk/`, remove unused code, check every module under 300 lines, rerun
`pytest -q` and coverage, write the summary in PROGRESS.md.

## After every phase
Run the phase's checks and all earlier tests. Paste exact output into PROGRESS.md.
Commit with the attribution line from the current system reminder. No push.

## Stop conditions
Parser unusable, a check that needs a hard rule broken, or the same check failing
three times after three different fixes. Write the blocker in PROGRESS.md and stop.

# SPEC2 plan

Phase 9: eight debts, in the order of SPEC2, one commit each. Done.

Phase 10: Describe(entity). Fixtures for Who is / What is read first: the wh variable has only an abstract restriction (person, thing), and the copula takes it in either argument slot.

Phase 11: read the three fixtures first (consequent is ARG1, antecedent ARG2 of the if-then predication). Rule family conditional.py, scope.clause, no new reading rules otherwise.

Phase 12: verify the statement half (already built); negated questions via per-atom polarity in ask and Match.

Phase 13: fixtures read (pron/pronoun_q, PERS NUM GEND on the variable). pronouns.py, mention table, notes on logical forms, Mind records mentions.

Phase 14: fixtures read (card with a digit CARG; how many is measure, much-many_a, abstr_deg, which_q). rules/numbers.py; Ask gets count and atleast.

Phase 15: fixtures read (and/or as a group variable or as an event conjunction). rules/coordination.py, Ask.alternatives.

Phase 16: fixtures read (unknown words are _surface/TAG_u_unknown). content.known_as, widening n/a for unknown words, UNKNOWN_WORD blames the word.

Phase 18: defaults, levels, defeat, policy, universal questions. defaults.py is new; engine rule_sql gets kind, level and bindings; Mind owns the policy setting.

Phase 19: Mind.retract, diagnose, observe, auto_revise, Forget that S. store.retract, revision table.

Phase 20: fixtures read (before/after predications, yofc, in_p_temp). rules/temporal.py, tense facts, Ask.tenses, built-in axioms, reuse_events.

Phase 21: fixtures read. rules/claims.py, Tell.claims/Ask.claims, claim table, claim contexts, Mind binds claims in questions.

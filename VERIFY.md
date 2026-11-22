# VERIFY: tolk (branch housekeeping, 73c605d) and SQUID (branch tolk-backend, 79e263f)

Everything below was run by me in `work/` from clean `git clone`s of the two local repositories. Nothing in either repository was changed. Raw outputs: `work/d/` (dialogues), `work/c_out.txt` (part c and d), my expectations `expected.md` (written, with a UTC timestamp, before any part c run).
Dialogue driver `work/drv.py` calls `Mind.hear` exactly as `scripts/repl.py` does and adds `suppose`, `drop`, `observe`, `diagnose`, `propose`, `read`; plain tier dialogues were also run through `scripts/repl.py` itself (`work/d/specAll.out`).

## Section a: install and tests

tolk:
```
git clone -b housekeeping /home/richarah/tolk tolk
cd tolk && uv venv --python 3.12 .venv && . .venv/bin/activate
sh scripts/setup_erg.sh          # ACE version 0.9.34, erg-2018.dat 283401864 bytes: downloaded fine
uv pip install -e '.[test]'      # `pip` is not present in a uv venv, so `uv pip` was used instead of `pip`
python -m pytest -q
  ...
  832 passed in 43.25s
```
SQUID:
```
git clone -b tolk-backend /home/richarah/squid squid
cd squid && uv venv --python 3.12 .venv && . .venv/bin/activate
uv pip install -e '.[dev]'       # README: pip install -e '.[dev]'; pulled tolk from git+https://github.com/richarah/tolk.git@housekeeping
                                 # (resolved to tolk==0.1.0 @ 73c605d3463c567442b6931b34dd9821cdf669aa = my tolk clone's HEAD; credentials worked)
export TOLK_ERG_DIR=<tolk clone>/erg
python -m pytest tests -q
  113 passed, 5 xfailed in 3.11s
python scripts/differential_tolk.py | tail -1
  15 questions, 0 disagreements
```
Matches the README numbers (113 passed, 5 expected failures; 15 questions, 0 disagreements). I did not rerun the Spider benchmark (needs the Spider data set, not on hand). Other checks: no module in tolk/ over 300 lines (largest 250); LICENSE and .github/workflows/tests.yml exist; `scripts/choice_table.py`, `code_removal.py`, `coverage.py` run without error.

Mismatches in section a: none.

## Section b: SPEC.md and SPEC2.md dialogues

Run in fresh stores in the spec's order. Lines not listed here matched.

### SPEC.md
Tier A dialogue (all 10 rows): match. "Does Tweety fly?" gives Yes with a 3-node proof (fly by rule 2, bird by rule 1, robin told). "Who is happy?" gives "Kim and Tweety". "Is Sandy happy?" Unknown. "Does Rex have an owner?" Yes (`have(rex, sk:6:x8:rex)`).
Tier B dialogue (all 11 rows): match. Pingu: No; after "Every penguin is a bird." a conflict is recorded and reported in the reply; "Does Pingu fly?" Conflict with both proofs; "Clark Kent is Superman." one thing, two names; "Does Clark Kent fly?" Yes; "Is the robin happy?" Yes; "The dog barks." `DEFINITE_MATCHES: 2 known things match`; "Tweety does not fly." refused, contradicts, proof shown.
Tier C dialogue (all 5 rows): match (past tense fact `tense(e1, past)` on Sandy's event).
Phase 6 (suppose "Tweety is a penguin." after tier B): Conflict inside, Yes outside, fact count 22 before and 22 after drop. This only holds with "No penguin flies." told as well (it is in the tier B sentence list, not in the dialogue table); without it, tier B has no rule giving a penguin a negative "flies", and the supposition does not conflict.
Phase 8: see item 1 below.

### Where a later phase changed a SPEC.md result (deliberate; I do not judge)
- SPEC.md tier A: "Birds are animals." is a strict rule. SPEC2 phase 18 says it becomes a default. Actual: `default _animal_n_1(X) :- _bird_n_1(X)`. Dialogue answers unchanged.
- SPEC.md tier C: "Does Kim live in Oslo?" etc unchanged. SPEC2 phase 20 adds "Sandy arrived." then "Does Sandy arrive?" Unknown: actual Unknown; "Did Sandy arrive?" Yes.
- SPEC.md "Choosing a reading" (refusals, then overlap, then parser order) and SPEC2 9.5 (refusals, store overlap, swallowed words, parser order). DECISIONS.md says the order was changed after an audit; the code (`tolk/choice.py`) is: eventive readings only; fewest generic-entry words; most store overlap; fewest swallowed words; then compile tied readings in parser order, where a `final` refusal ends the search. Refusal is therefore not a ranking criterion before overlap. (Effect: see item 7.)
- SPEC.md phase 4 / REVIEW: negated question was refused in the review, now answered (SPEC2 12): matches SPEC2.

### SPEC2.md dialogues (all rows run; differences only)
- Phase 10 "Who is Tweety?", "What is Kim?" list told then derived facts; "Who is Zed?" Unknown: match.
- Phase 11 three sentences stored as ground/variable rules and answer correctly: match. ("If Luna paints, Bruno is happy." fails: item 7.)
- Phase 12 dialogue (5 questions): match (No with proof, Unknown, Yes, Unknown).
- Phase 13: "Am I a person?" Yes, "Are you a cat?" Unknown, "It sings." stores `sing(tweety)` with `it = tweety` shown, "She is happy." after "Kim likes Sandy." refused `AMBIGUOUS_PRONOUN: sandy or kim`: match.
- Phase 14: 2, Yes, Unknown, 3; digits ("Kim owns 4 birds." gives 4); "most", "more than two" refused. "Kim owns half of the cats." is refused, but as `DEFINITE_MATCHES: 3 known things match`, not as a fraction (spec: fractions are refused; it is refused, reason differs).
- Phase 15: "Kim and Sandy are happy." 2 facts; "Or" in a statement refused; "Does Kim sing or dance?" works: match.
- Phase 16: "Tweety is a blorp." `_blorp_n_unknown`; "Every blorp flibbers."; "Does Tweety flibber?" Yes: pass (first alternative).
- Phase 17: `tolk.read("Does Kim own a dog?")` returns the Ask; `tolk.read("Kim can sing.")` returns `refuse UNSUPPORTED_PREDICATE: _can_v_modal`: match.
- Phase 18 dialogue: Tweety Yes; Pingu "No ... defeated "Birds fly." (rule 1) by specific"; `TOLK_POLICY=` empty: Conflict; "Tweety does not fly." stored, then No: match. Universal questions: "Is every penguin a bird?" Yes; "Does every bird fly?" "Yes, by default"; "Is every robin a bird?" Unknown (no rule told). See item 2.
- Phase 19: diagnose lists "Every penguin is a bird.", "Every bird flies.", "Pingu does not fly.", "Pingu is a penguin."; "Forget that every bird flies." then Pingu No and Tweety Unknown: match. Observation `Pingu does not fly.` stays, conflict reported with 3 candidates, none an observation; with `TOLK_AUTO_REVISE=1` retracts "Every bird flies.": match.
- Phase 20: lived/live Unknown, did Yes; before chain Yes, reverse No; "Where did Kim live in 2019?" Oslo; future/perfect/progressive refused: match.
- Phase 21: Unknown, Yes, Unknown; "Who believes ..." Kim; "What does Kim believe?" lists; nested claim refused: match.
- Phase 22: Yes, No, Unknown, "Kim (among those I know)"; "as tall as" refused: match.
- Phase 23: "Rex is unglorpy." / "Is Rex glorpy?" No; "Pingu is a flibberer." / "Does Pingu flibber?" Yes; "Tweety is flibberable." stored with `flibberable = able + flibber`, no rule: match.
- Phase 24 (`TOLK_WORDING=generated`, tier A): one-place verb and "is a" facts are generated ("Tweety flies.", "Tweety is a bird."); `own(kim, a1)`, `sk:6:x8:rex is an owner` fall back to the template. Match with the spec (at least those two patterns).

### PROMPT.md items
1. "If Rio hums, Pip hums." becomes a rule (reading 6 of 25): match.
2. closed_world on: "Does Tweety fly?" No, "Who flies?" Nothing; off: Unknown; "Is every robin a bird?" Unknown either way: match.
3. Unknown words: see item 4.
6. "Kim sings and Sandy dances." two statements: match. 7: generated wording per fact with template fallback: match.
Housekeeping: "What is a robin/bird/dog?" give rules, "Known: n: ..." with names; "What is a fish?" / "a zebra" Unknown; "I love Veronika." "What is love?" gives `(widened: love (noun) matched as love (verb))` and `love(you, veronika)`; spelling: "Twety sings." refused POSSIBLE_TYPO suggesting tweety, sent again stored; "Tweety is a robbin." refused suggesting robin; "Tweedy sings." refused; "Kim sings." stored: all match. LICENSE and CI file exist.
SQUID items (README-level): legacy not called from anywhere (grep); invented table names `blorp`, `quux`, `frob` compile ("Which quuxes does Kim frob?" returns the right row; verified by executing the SQL); differential script 15/15: match, except item 12.

### Mismatches found in section b
1. Phase 8, "four things that share two predicates yields exactly one proposal." With four things each told "X is a robin." and "X is a bird." (identical extensions), `Mind.propose()` returns `[]`. Cause: `tolk/proposals.py` also requires Q to have a member P lacks. `tests/test_propose.py` passes only because it adds a fifth bird ("Zed"). Command: tell Tweety, Pip, Rio, Kim each robin and bird, then `!propose`: no output.
2. Phase 18 universal questions: spec says "If its opposite follows, `No`." Actual for "Do all penguins fly?" (store: Birds fly. Every penguin is a bird. Penguins do not fly.): `No, by default`.
3. Phase 5 "where" questions: "Bob is in Paris." then "Where is Bob?" gives `Unknown` (the question atom `_*_p_[ls]*(bob, X)` has two arguments, the copular fact `_in_p_loc(e1, bob, paris)` three). "Is Bob in Paris?" is Yes. DECISIONS.md records this as "Not fixed". Where-questions with a verb ("Where does Kim live?") work.
4. PROMPT item 3: "Tweety is a blips." (and "Rex is a blips.") is not stored and not refused UNKNOWN_WORD: `reading 1 of 0 / refuse NO_EVENT_READING: none of the readings has a predicate on the sentence event`. ("Tweety blips." stores `_blip_v_unknown`. "Tweety toves.", "Tweety is a tove." are refused UNKNOWN_WORD, which the item allows. The other eight words store with a class.)
5. Hard rule 5 / SPEC2 9 ("a refusal is a normal return value, not an exception"): `Mind.hear("List the section_name in reversed lexicographical order.")` raises `delphin.mrs._exceptions.MRSSyntaxError: expected: a feature` (the parser's MRS contains `_section_name/NN_u_unknown`). The repl survives it as specified (prints "internal error, see stderr; continuing", traceback on stderr, exit 0). The library call raises. (SQUID's README notes the same case.)

## Section c: my 40 sentences

`expected.md` was saved first. Each sentence run alone on a fresh Mind, on E (empty) and A (the 12 tier A statements). Result tables: `work/c_out.txt`. Everything not mentioned below matched my expectation on both stores (W1-W6, W8-W16 except noted, W18, W19, W21-W25; R1-R6, R8, R9, R10 (E stored, A POSSIBLE_TYPO), R11 (E stored, A refused with proof), R12-R15).

Mismatches:
6. W7 "If Luna paints, Bruno is happy." expected a ground rule. Actual, E and A: `reading 1 of 5 / refuse UNSUPPORTED_PREDICATE: _if_x / refused`. Same for "If Luna paints, Bruno sings." and "Bruno is happy if Luna paints."; "If Luna sings, Bruno is happy." and "If Kim sings, Sandy dances." work. Reading 2 compiles to the right rule (`rule _happy_a_with(E!, bruno) :- _paint_v_1(E1, luna)`); see section d.
7. W20 "Ola and Mina are teachers." expected two facts (like "Ola and Mina are happy.", which does give 2). Actual: `refuse UNCONSUMED: no atom uses x20`. Same for "Ola and Mina are otters."
8. W17 "I am a teacher." expected `_teacher_n_1(user)`; actual `tell _teacher_n_of(user)` (the grammar's sense for "teacher"; my expectation of the sense name was a guess, the fact is stored correctly with `I = user`). Expectation-level mismatch only.
9. R7 "Ola owns more than two cellos." refused as expected, but with code `UNKNOWN_WORD: cellos` instead of `UNSUPPORTED_PREDICATE more_comp` (the refusal of reading 1 is relabelled because the word `cellos` is unknown; "Ola owns three cellos." is stored with `_cello_n_unknown`, so the word is accepted without "more than"). With a known noun ("Kim owns more than two cats.") the code is `more_comp`. Latent: reading 3 of that sentence compiles to a Tell that drops "more than" (`_own_v_1(e1, ola, a1)`, `a2`, `_more+than_a_1(e2)`), which stays unused only because reading 1's refusal is final.
10. Found while probing (outside the 40): `Every dog that does not bark is quiet.` is stored (reading 9 of 17, via the 25-reading wide search) as `default _quiet_a_1(E!, X) :- _dog_n_1(Y), _do_v_1(E1, Y), _not_c(X, Y, Z), _bark_n_1(Z)` and replies "rule stored". The rule is wrong (a default, with a noun "bark" and a grammar predicate `_not_c` in the body); "Rex is a dog." then "Is Rex quiet?" is Unknown. "Every cat that does not purr is grumpy." likewise (`... _not_c(X, Y, Z), _purr_n_1(Z)`). Hard rule 5 (never guessed at).
11. SQUID (extra, schema from section b test): `squid.compile("Does Kim not frob Yo?", schema)` raises `SquidCompileError UNKNOWN_WORD: frob`, while "Does Kim frob Zed?" and "Which quuxes does Kim frob?" compile with the same schema (invented verb-table `frob`). The README says "Does Kim not own Fido?" compiles; the invented-table negated case does not.

## Section d: sentences with more than one reading

For each of my 40 sentences (run on E, with the same ties on A) I listed every reading with `tolk.erg.parse`-level readings (`words.parse`, `sem.read`), its compile result, the measures (generic, overlap, swallowed) and the set tied by `choice.preferred`. Full listing: `work/c_out.txt` (lines starting `readings=` / `R1 ...`). Verdicts (chosen reading vs the right one):

- Right reading chosen: W3 (verb "paints", R2; R1 is the grammar's fallback), W5, W6, W11 (R1; R2/R5 are the identity sense, refused), W13 (`in_p_loc`; R4 is the `in_p_state` sense), W14 (`in_p_loc` plus `in_p_temp` on e1; R4/R5 attach "in 2015" to a second event), W15 (R1 and R2 give the same facts), W16, W19 (R1; R2-R4 demonstrative "that"), W21, W22, W12 (R1 and R2 give the same Describe), and every refused sentence R1-R6, R8, R9, R10, R11, R13-R15 (all readings refuse, or the compiling ones are the right one).
- Wrong reading chosen: W7 "If Luna paints, Bruno is happy." Tied set [1, 2, 3]. R1 reads "if" as a preposition and "paints" as a noun (`_if_x`, `_paint_n_1`) and gives the final refusal `UNSUPPORTED_PREDICATE: _if_x`, which ends the search; R2 (`_if_x_then`, `_paint_v_1`) compiles to the correct rule and is never tried. Same on A.
- R7: right reading is one of the refusing ones (R1/R2); chosen R1; R3 (compiles to a Tell without "more than") is not chosen (see 9).
- W20: one reading only; refused UNCONSUMED (not a choice problem).

Mismatches in section d: 1 (W7, same defect as item 6; counted once in the list below).

## Final list of mismatches

Section a: 0.
Section b: 5 (items 1-5).
Section c: 6 (items 6-11; items 10 and 11 were found outside the 40 sentences, 8 is expectation-level only).
Section d: 1 (W7 wrong reading; the same root as item 6, so the total below counts it once).

1. Phase 8: identical extensions give no proposal (`propose()` returns []).
2. Phase 18: "Do all penguins fly?" gives "No, by default"; spec says "No".
3. Phase 5: "Where is Bob?" after "Bob is in Paris." is Unknown (documented as open in DECISIONS.md).
4. PROMPT 3: "Tweety is a blips." is neither stored nor refused UNKNOWN_WORD (NO_EVENT_READING, 0 readings).
5. Hard rule 5: `Mind.hear` raises `MRSSyntaxError` on "List the section_name in reversed lexicographical order."
6. "If Luna paints, Bruno is happy." refused `_if_x`; the correct reading 2 compiles but a final refusal on reading 1 ends the search (also section d).
7. "Ola and Mina are teachers." / "... are otters." refused UNCONSUMED (noun complement under coordination).
8. "I am a teacher." stores `_teacher_n_of`, my expectation `_teacher_n_1` (expectation-level).
9. "Ola owns more than two cellos." refused with UNKNOWN_WORD: cellos instead of more_comp; a compiling reading drops "more than".
10. "Every dog that does not bark is quiet." and "Every cat that does not purr is grumpy." store a wrong default/rule with `_not_c` and a noun in the body.
11. SQUID: "Does Kim not frob Yo?" refused UNKNOWN_WORD: frob for an invented table.

Not counted (deliberate, documented changes): "Birds are animals." default; "Does Sandy arrive?" Unknown; reading-choice order replaced (DECISIONS.md, SPEC2 9.5 criteria order not followed literally).
Could not run: Spider benchmark (data set absent).

---
# Round 2 (fresh verifier, new sentences; run after the round 1 fixes; not fixed, by instruction)

# VERIFY (second independent verifier)

Work directory: `.../verify2/work/` (clones `tolk` at 9c8f11c on `housekeeping`, `squid` on `tolk-backend`). Inputs and raw outputs of every
run are in `work/d/`. Nothing in either repository was modified. I read nothing from verify1.

## a. Install and tests

tolk:
```
git clone -b housekeeping /home/richarah/tolk tolk
cd tolk && uv venv --python 3.12 && sh scripts/setup_erg.sh && uv pip install -e '.[test]'
python -m pytest -q          ->  841 passed in 44.12s
```
(setup_erg.sh downloaded ace and erg-2018.dat into erg/ without error.)

SQUID:
```
git clone -b tolk-backend /home/richarah/squid squid
cd squid && uv venv --python 3.12 && uv pip install -e '.[dev]'   # README's documented command; pulled tolk from github.com/richarah/tolk.git@housekeeping (resolved to 9c8f11c, same as the local head)
export TOLK_ERG_DIR=<tolk clone>/erg
python -m pytest -q          ->  113 passed, 5 xfailed in 3.12s
```
Mismatches in a: 0. Also seen: LICENSE (MIT) and `.github/workflows/tests.yml` exist in tolk; `legacy` is referenced by no module except a comment in `squid/__init__.py`; tolk's `meta` table holds policy, auto_revise, closed_world, wording.

## b. SPEC.md and SPEC2.md dialogues through scripts/repl.py

Inputs: `work/d/*.txt`; outputs `work/d/out1.txt` and others. Settings by TOLK_POLICY / TOLK_AUTO_REVISE / TOLK_CLOSED_WORLD / TOLK_WORDING.

Matching the tables line by line (no difference): tier A (all 10 answers, "Does Tweety fly?" proof is fly <- bird <- robin, three steps); tier B (all 11 rows,
including the conflict row on telling "Every penguin is a bird.", "Clark Kent is Superman." as one thing, "The dog barks." DEFINITE_MATCHES, "Tweety does not fly." refused with proof);
tier C (all 5 rows, "Sandy arrived." stores `tense(e1, past)`); phase 6 (suppose "Tweety is a penguin." after tier B including "No penguin flies.": Conflict inside, Yes outside, fact count 21 = 21 after drop);
phase 10 Describe, Unknown for an unknown name; phase 11 the three conditionals; phase 12 dialogue (No, Unknown, Yes, Unknown); phase 13 (Am I a person Yes, Are you a cat Unknown, "It sings." stores Tweety, "She is happy." AMBIGUOUS_PRONOUN, resolution shown `it = tweety`);
phase 14 (2, Yes, Unknown, then 3); phase 15 "Kim and Sandy are happy." (two facts), "Or" in a statement refused; phase 16 (Does Tweety flibber? Yes); phase 18 (Yes; "No ... defeating Birds fly. by specific"; TOLK_POLICY= empty gives Conflict; told fact defeats default; trusted and recent policies each give the expected winner);
phase 19 (diagnose lists exactly the four sentences; "Forget that every bird flies." then Pingu No, Tweety Unknown; auto_revise retracts and says so; observe is never retracted);
phase 20 (Unknown for Does Kim live in Oslo? after "lived"; Yes for Did; before/after chain Yes and No; "Where did Kim live in 2019?" Oslo; "Does Sandy arrive?" Unknown);
phase 21 (Unknown, Yes, Unknown; who/what listed); phase 22 (Yes, No, Unknown, Kim among those I know); phase 23 (Is Rex glorpy? No; Does Pingu flibber? Yes; flibberable stored, split shown, no rule);
PROMPT part 1: closed_world on gives No / Nothing, off gives Unknown; "If Rio hums, Pip hums." is a rule (reading 6 of 25); "Kim sings and Sandy dances." two facts; wording=generated words proofs ("Tweety flies."); spelling dialogue exactly as specified
(Twety refused suggesting Tweety, second send stores Twety, "robbin" suggests robin, "Tweedy" refused, "Kim sings." stored); DescribeKind for "What is a fish?" (rules, "Known: 2: Dory, Nemo"), "What is love?" after "I love Veronika." (widening shown, love(you, veronika)), unknown word gives Unknown;
phase 2 repeat ("already told"); SQUID differential and README claims not rerun beyond the tests above (113 pass).

Differences found:

1. Phase 15 (SPEC2: ""Or" in a question is `Yes` if either side is."). Store: "Kim is happy."
   ```
   $ printf 'Kim is happy.\nIs Kim happy or Lee happy?\n' | python scripts/repl.py
   Is Kim happy or Lee happy?
     reading 1 of 5
     refuse UNCONSUMED: no atom uses x13
     refused
   ```
   Other or-questions work: "Is Kim happy or sad?" Yes, "Is Kim or Lee happy?" Yes, "Does Kim like Sandy or Lee?" Unknown.
2. Phase 8 (SPEC: "a test with four things that share two predicates yields exactly one proposal"). Ann, Bob, Cy, Dee each told "is a robin" and "is a bird":
   `Mind.propose()` returns `[]` (zero, not one). With a fifth thing that is only a bird it returns `Is every robin a bird?`; with the four things sharing robin and happy it also returns `[]`.
   (Script `work/d/api2.py`.)
3. PROMPT item 3 (unknown word is stored with the right class or refused UNKNOWN_WORD). Word "blips" in the noun frame:
   ```
   Tweety is a blips.   -> reading 1 of 0 / refuse NO_EVENT_READING: none of the readings has a predicate on the sentence event / refused
   Blips are things.    -> refuse EMPTY_RULE_BODY: the restriction has no atom
   ```
   Neither is UNKNOWN_WORD, and the repl prints "reading 1 of 0". ("Tweety blips." and "Tweety is blips." are stored as `_blip_v_unknown` / `_blip_n_unknown`; the other nine listed words behave: frant, snerk, tove, greeb refused UNKNOWN_WORD as verbs and stored as `_x_a_unknown` as adjectives; quorl, drabbles, wug, plonth stored as nouns; mimsy stored as adjective; "Every blorp flibbers." stored a rule.)
4. Hard rule 5 / SPEC "A refusal is a normal return value, not an exception", and SPEC2 phase 9 "the repl never exits". Same word:
   ```
   A blips sleeps.
     internal error, see stderr; continuing
   IndexError: list index out of range   (tolk/mind.py line 138, spelling.check(self.db, text, readings[k]) with readings empty)
   ```
   The repl survives (as specified) but `Mind.hear` raises instead of returning a refusal.
5. Arguable, PROMPT item 3 ("storing an invented common word as a name is a failure"): `Quorl is a thing.` stores `_thing_n_of-about(quorl)`, the invented word as a named thing. It is capitalised and sentence-initial, so it may be taken as a name; I count it as a note, not a mismatch.

Where a later phase changed an earlier dialogue deliberately: "Birds are animals." is now `default _animal_n_1(X) :- _bird_n_1(X)` (SPEC2 phase 18 says so; answers unchanged);
"Sandy arrived. / Does Sandy arrive?" is Unknown (SPEC2 phase 20 says so). "Where does Kim live?" prints the predicate as `_*_p_[ls]*` (a wildcard over preposition senses); the answer Oslo is as in SPEC.md.

Observation, outside the spec: with a schema whose table is `gizmo` and a row named "Ga", `squid.compile("Which wobbles does Ga zap?")` gives SQL comparing the name with 'georgia' (the grammar expands "Ga" to Georgia) and returns no rows; no refusal. With the name "Gus", the invented table names `gizmo`, `wobble`, `zaps` work (rows returned correctly).

## c. My 40 sentences

Expectations: `verify2/expected.md`, written and saved before any run. Outputs: `work/d/mine_empty.out`, `mine_tierA.out` (tier A tells first), `mine_closed.out` (closed_world on); SQUID run `work/d/sq.py`.

Result: all 25 should-work and all 15 should-refuse sentences gave the expected result on the empty store. On the tier A store the outcomes were identical (diff of the two outputs: only rule numbers in proofs, and which anonymous horses a1..a3 or a2..a4 appear in the proof of "How many horses does Ada own?"; the count is 3 in both). Closed world: only W22 "Is Moe a pig?" changed, Unknown to No, as expected.
Highlights: W16 to W18 an unknown noun and verb stored with `_unknown` class and "Does Moe trundle?" Yes; W11 DescribeKind lists the rule and "Known: 1: Moe"; W12 Unknown; W21 `reading 6 of 25`; R1 `UNSUPPORTED_PREDICATE: _might_v_modal`, R2 `UNSUPPORTED_TENSE: fut`, R3/R4 `UNSUPPORTED_ASPECT`, R5 `COORDINATION`, R6 `comp_equal`, R7 `_most_q`, R8 `more_comp`, R9 `POSSIBLE_TYPO: bixbi: did you mean bixby?`, R10 `DEFINITE_MATCHES: 2`, R11 `AMBIGUOUS_PRONOUN`, R12 nested claim, R13 refused with proof of "Moe squeaks".
SQUID (schema pupil, book, borrows; rows as in expected.md): W23 rows Dune, Emma; W24 2; W25 no row (empty result); R14 `SquidCompileError NOT_A_QUESTION: Tell`; R15 `SquidCompileError UNSUPPORTED_QUESTION: ... past tense`.
Mismatches in c: 0.

## d. Readings

Script `work/d/rd.py` (tolk.erg via words.parse, sem.read, compile.compile_reading of every reading, chosen reading starred); output `work/d/readings.txt`. Reading numbers were the same on the empty and tier A stores.
Sentences with more than one reading: 27 of my 38 told lines. In each, the chosen reading is the right one; every other reading was a refusal (FALLBACK_PARSE, GRAMMAR_ARTIFACT, UNSUPPORTED_*) or a duplicate of the chosen logical form, except:
- "Ada owns more than three horses." reading 3 compiles to a Tell with a `_more+than_a_1` atom; it is not chosen because reading 1 is a final refusal. Correct outcome (storing reading 3 would be wrong).
- "Zoe does not like cheese." reading 4 is a different rule (`_do_v_1 ... not _like_p`); reading 1 chosen, which is right.
- "Ada hums and Bix whistles." chosen reading 11; readings 1 to 10 are FALLBACK_PARSE refusals; 11 is right.
- "If Ola hums, Pia hums." chosen 6 of 25 (widened); 6 is the one conditional that compiles, and it is right.
Mismatches in d: 0.

## Final list of mismatches

1. (b) Phase 15: "Is Kim happy or Lee happy?" refused UNCONSUMED although "or" in a question should be Yes if either side is.
2. (b) Phase 8: four things sharing two predicates yield zero proposals, not exactly one.
3. (b) PROMPT item 3: "Tweety is a blips." refused NO_EVENT_READING ("reading 1 of 0"), and "Blips are things." EMPTY_RULE_BODY, instead of UNKNOWN_WORD or a stored class.
4. (b) "A blips sleeps." raises IndexError inside `Mind.hear` (tolk/mind.py:138) instead of returning a refusal.

Per section: a 0, b 4 (plus one arguable note and one SQUID observation), c 0, d 0.

---
# What was done about round 1 (by the builder, after round 1)
| # | Mismatch | Outcome |
|---|---|---|
| 1 | proposals with identical extensions | open: with equal extensions both directions are equally supported, so the pair gives no proposal by design (test_propose adds a fifth bird); SPEC's "exactly one" is not met for that store |
| 2 | "Do all penguins fly?" gives "No, by default" | open: the penguin rule is itself a default ("Penguins do not fly."), so "by default" is the phase 18 marking; SPEC says "No" |
| 3 | "Where is Bob?" | fixed (test_verify1.py::test_3) |
| 4 | "Tweety is a blips." | open: ungrammatical ("a" + plural), no reading even with classes offered, so NO_EVENT_READING; the item's forms ("Tweety blips.") work |
| 5 | MRSSyntaxError on an underscored word | fixed (tests/test_underscore.py): refused UNKNOWN_WORD |
| 6 | "If Luna paints, Bruno is happy." | fixed (test_verify1.py::test_6) |
| 7 | "Ola and Mina are teachers." | fixed (test_verify1.py::test_7) |
| 8 | "I am a teacher." sense name | not a defect: the verifier's guess of the sense name was wrong |
| 9 | "more than two cellos" relabelled UNKNOWN_WORD | open: the relabelling is by design; the latent reading beyond the first five is not reachable |
| 10 | wrong rule with `_not_c` | fixed (test_verify1.py::test_10): refused SCOPE_AMBIGUOUS |
| 11 | SQUID "Does Kim not frob Yo?" | not a defect found: "Yo" is a word of the grammar; the same refusal comes without "not" |

## Verification round 3 (v0.1.3)

An independent agent re-checked the features of the v0.1.3 work against their documentation, by probes, without the author's conclusions. Probes ran against `master` at `acd7fb4`.

## Fixed in this round (branch `fix-modal-generics`, tests/test_modal_generics.py)
- "Birds can fly." was stored as one unnamed bird with a modal. A modal over a generic (a bare plural, every, all) is now refused UNSUPPORTED_PREDICATE, as a modal in a rule.
- "Every bird can fly." was refused with the quantifier label. Now the same modal refusal.

## Open, recorded (not fixed)
- Control with a verb the grammar reads as a noun: "Lee tries to dance." reads "dance" as a noun, so no claim is stored (a reading choice limit; the grammar offers the noun reading).
- Conjoined infinitives: "Kim wants to sing and dance." stores one claim with the conjunction in its content, so "Does Kim want to sing?" is Unknown. Expected: Yes. Open.
- Robustness: a second `suppose` while one is open raises ValueError, and `drop()` with nothing open raises ValueError. These are API errors for the caller, documented as one level of supposition; they are not raised by any sentence.
- A supposition that contradicts a told fact ("Kim sings." then suppose "Kim does not sing.") answers Conflict. Undocumented; left as it is.
- Generated wording falls back to the template for "a dog" (`own(kim, a1)`, `a1 is a dog`): anonymous things have no name for the grammar to say. Documented in DECISIONS.md proofs item.

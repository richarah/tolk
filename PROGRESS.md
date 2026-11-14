# PROGRESS

## Phase 0: parser and fixtures

Checks run:

```
$ .venv/bin/pytest -q
........................................................................ [ 90%]
........                                                                 [100%]
(count superseded: see the latest entry)
```

Setup:

```
$ sh scripts/setup_erg.sh
ACE version 0.9.34
compiled at 18:11:19 on Jan 21 2021
-rw-rw-r-- 1 richarah richarah 283401864 Nov 14 21:13 erg-2018.dat
```

Output of `scripts/record.py --force`:

```
reading(s): Tweety is a robin.
reading(s): Every robin is a bird.
reading(s): Every bird flies.
reading(s): Birds are animals.
reading(s): Tweety sings.
reading(s): Every robin that sings is happy.
reading(s): Kim is a person.
reading(s): Kim owns a dog.
reading(s): Every person who owns a dog is happy.
reading(s): Kim likes Sandy.
reading(s): Rex is a dog.
reading(s): Every dog has an owner.
reading(s): Does Tweety fly?
reading(s): Is Tweety a bird?
reading(s): Is Tweety an animal?
reading(s): Is Tweety happy?
reading(s): What flies?
reading(s): Which robin sings?
reading(s): Who is happy?
reading(s): Who likes Sandy?
reading(s): Who does Kim like?
reading(s): Is Sandy happy?
reading(s): Does Rex have an owner?
reading(s): Pingu is a penguin.
reading(s): Pingu does not fly.
reading(s): No penguin flies.
reading(s): Every penguin is a bird.
reading(s): Clark Kent is Superman.
reading(s): Superman flies.
reading(s): Does Pingu fly?
reading(s): Does Clark Kent fly?
reading(s): Is the robin happy?
reading(s): The dog barks.
reading(s): Tweety does not fly.
reading(s): Kim lives in Oslo.
reading(s): Sandy arrived.
reading(s): Who lives in Oslo?
reading(s): Where does Kim live?
reading(s): Does Kim live in Oslo?
reading(s): Does Kim live in Bergen?
```

First reading of three fixtures, pasted from `tests/fixtures/*.json`:

### Tweety is a robin.

```
[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ proper_q<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]  [ named<0:6> LBL: h7 CARG: "Tweety" ARG0: x3 ]  [ _be_v_id<7:9> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x9 [ x PERS: 3 NUM: sg IND: + ] ]  [ _a_q<10:11> LBL: h10 ARG0: x9 RSTR: h11 BODY: h12 ]  [ _robin_n_1<12:18> LBL: h13 ARG0: x9 ] > HCONS: < h0 qeq h1 h5 qeq h7 h11 qeq h13 > ICONS: < > ]
```

### Every robin that sings is happy.

```
[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ _every_q<0:5> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]  [ _robin_n_1<6:11> LBL: h7 ARG0: x3 ]  [ _sing_v_1<17:22> LBL: h7 ARG0: e8 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] ARG1: x3 ARG2: i9 ]  [ _happy_a_with<26:32> LBL: h1 ARG0: e2 ARG1: x3 ARG2: i10 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ICONS: < > ]
```

### Who does Kim like?

```
[ LTOP: h0 INDEX: e2 [ e SF: ques TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ person<0:3> LBL: h4 ARG0: x5 [ x PERS: 3 NUM: sg ] ]  [ which_q<0:3> LBL: h6 ARG0: x5 RSTR: h7 BODY: h8 ]  [ proper_q<9:12> LBL: h9 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h10 BODY: h11 ]  [ named<9:12> LBL: h12 CARG: "Kim" ARG0: x3 ]  [ _like_v_1<13:18> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x5 ] > HCONS: < h0 qeq h1 h7 qeq h4 h10 qeq h12 > ICONS: < > ]
```

## Phase 1: logical form and core mapping (tier A)

Built `tolk/lf.py`, `tolk/compile.py`, `tolk/rules/{names,quant,copula,content}.py`. Every family exposes `map_ep(ctx, ep)` returning atoms, `None` (not mine), or a refusal. `compile.py` tries the families in one fixed order.

Checks, exact output:

```
$ .venv/bin/pytest -q tests/test_compile.py tests/test_lf.py
(count superseded: see the latest entry)
$ .venv/bin/pytest -q
(count superseded: see the latest entry)
```

All tier A sentences compile to the expected printed form (table at the top of `tests/test_compile.py`). The lemma scan passes after the function-word exemption described in DECISIONS.md.

## Phase 2: store and engine

Built `tolk/store.py` and `tolk/engine.py`. The engine compiles each rule to SQL, one `INSERT OR IGNORE ... SELECT` per head atom plus one skolem `entity` insert per created variable and one `why` insert per head atom. Every value is a bound parameter. Rounds are semi-naive as the spec describes.

Checks, exact output:

```
$ .venv/bin/pytest -q -s tests/test_engine.py
fixpoint: 300000 derived facts in 1.29s
(count superseded: see the latest entry)
$ .venv/bin/pytest -q
(count superseded: see the latest entry)
```

The 50,000-fact timing is the `fixpoint` line above.

## Phase 3: questions, proofs, wording, repl

Built `tolk/ask.py`, `tolk/say.py`, `tolk/mind.py`, `scripts/repl.py`. `ask.py` reuses `engine.Match`, the FROM/WHERE generator that rules also use. `say.py` is stiff: facts show as predicate and arguments; the article is chosen from the lemma.

Checks, exact output:

```
$ .venv/bin/pytest -q
(count superseded: see the latest entry)
```

The tier A dialogue run through the repl (`scripts/repl.py`), exact output:

```
Tweety is a robin.
  reading 1 of 2
  tell   _robin_n_1(tweety)
  stored, 1 new fact(s)
Every robin is a bird.
  reading 1 of 2
  rule   _bird_n_1(X) :- _robin_n_1(X)
  rule stored
Every bird flies.
  reading 2 of 2
  rule   _fly_v_1(E!, X) :- _bird_n_1(X)
  rule stored
Birds are animals.
  reading 1 of 1
  rule   _animal_n_1(X) :- _bird_n_1(X)
  rule stored
Tweety sings.
  reading 1 of 1
  tell   _sing_v_1(e1, tweety)
  stored, 1 new fact(s)
Every robin that sings is happy.
  reading 1 of 5
  rule   _happy_a_with(E!, X) :- _robin_n_1(X), _sing_v_1(E1, X)
  rule stored
Kim is a person.
  reading 1 of 1
  tell   _person_n_1(kim)
  stored, 1 new fact(s)
Kim owns a dog.
  reading 1 of 1
  tell   _own_v_1(e1, kim, a1)
tell   _dog_n_1(a1)
  stored, 2 new fact(s)
Every person who owns a dog is happy.
  reading 1 of 1
  rule   _happy_a_with(E!, X) :- _person_n_1(X), _own_v_1(E1, X, Y), _dog_n_1(Y)
  rule stored
Kim likes Sandy.
  reading 1 of 1
  tell   _like_v_1(e1, kim, sandy)
  stored, 1 new fact(s)
Rex is a dog.
  reading 1 of 1
  tell   _dog_n_1(rex)
  stored, 1 new fact(s)
Every dog has an owner.
  reading 1 of 1
  rule   _have_v_1(E!, X, Y!), _owner_n_of(Y) :- _dog_n_1(X)
  rule stored
Does Tweety fly?
  reading 1 of 5
  ask    _fly_v_1(E, tweety)
  Yes
fly(tweety)  (by rule 2)
  tweety is a bird  (by rule 1)
    tweety is a robin  (told: "Tweety is a robin.")
Is Tweety an animal?
  reading 1 of 5
  ask    _animal_n_1(tweety)
  Yes
tweety is an animal  (by rule 3)
  tweety is a bird  (by rule 1)
    tweety is a robin  (told: "Tweety is a robin.")
Is Tweety happy?
  reading 1 of 5
  ask    _happy_a_with(E, tweety)
  Yes
happy(tweety)  (by rule 4)
  tweety is a robin  (told: "Tweety is a robin.")
  sing(tweety)  (told: "Tweety sings.")
What flies?
  reading 1 of 3
  ask X  _fly_v_1(E, X)
  Tweety
fly(tweety)  (by rule 2)
  tweety is a bird  (by rule 1)
    tweety is a robin  (told: "Tweety is a robin.")
Which robin sings?
  reading 1 of 2
  ask X  _robin_n_1(X), _sing_v_1(E, X)
  Tweety
tweety is a robin  (told: "Tweety is a robin.")
sing(tweety)  (told: "Tweety sings.")
Who is happy?
  reading 1 of 1
  ask X  _happy_a_with(E, X)
  Kim and Tweety
happy(kim)  (by rule 5)
  kim is a person  (told: "Kim is a person.")
  own(kim, a1)  (told: "Kim owns a dog.")
  a1 is a dog  (told: "Kim owns a dog.")
happy(tweety)  (by rule 4)
  tweety is a robin  (told: "Tweety is a robin.")
  sing(tweety)  (told: "Tweety sings.")
Who likes Sandy?
  reading 1 of 1
  ask X  _like_v_1(E, X, sandy)
  Kim
like(kim, sandy)  (told: "Kim likes Sandy.")
Who does Kim like?
  reading 1 of 2
  ask X  _like_v_1(E, kim, X)
  Sandy
like(kim, sandy)  (told: "Kim likes Sandy.")
Is Sandy happy?
  reading 1 of 5
  ask    _happy_a_with(E, sandy)
  Unknown
Does Rex have an owner?
  reading 1 of 2
  ask    _have_v_1(E, rex, X), _owner_n_of(X)
  Yes
have(rex, sk:6:x8:rex)  (by rule 6)
  rex is a dog  (told: "Rex is a dog.")
sk:6:x8:rex is an owner  (by rule 6)
  rex is a dog  (told: "Rex is a dog.")
```

## Phase 4: negation, "no", identity, definites (tier B)

Built: negative atoms (`Atom.positive`), `rules/neg.py`, the `_no_q` rule shape (universal with a negated head), definites resolved through a store lookup, identity as `Same` merged in the store, negation as failure in rule bodies with the spec's safety and stratification checks, contradiction refusal at tell time, and conflict rows after each engine run.

Checks, exact output:

```
$ .venv/bin/pytest -q tests/test_dialogue_b.py
(count superseded: see the latest entry)
$ .venv/bin/pytest -q
(count superseded: see the latest entry)
```

The tier B dialogue through `Mind` (the repl transcript; "No penguin flies." is not in the spec's dialogue table, so it is not told here; its compiled form is tested separately):

```
Pingu is a penguin.
  reading 1 of 1
  tell   _penguin_n_1(pingu)
  stored, 1 new fact(s)
Pingu does not fly.
  reading 1 of 4
  tell   not _fly_v_1(_, pingu)
  stored, 1 new fact(s)
Does Pingu fly?
  reading 1 of 5
  ask    _fly_v_1(E, pingu)
  No
  not fly(pingu)  (told: "Pingu does not fly.")
Every penguin is a bird.
  reading 1 of 1
  rule   _bird_n_1(X) :- _penguin_n_1(X)
  rule stored
Does Pingu fly?
  reading 1 of 5
  ask    _fly_v_1(E, pingu)
  Conflict
  fly(pingu)  (by rule 2)
    pingu is a bird  (by rule 7)
      pingu is a penguin  (told: "Pingu is a penguin.")
  not fly(pingu)  (told: "Pingu does not fly.")
Clark Kent is Superman.
  reading 1 of 1
  same   clark_kent = superman
  one thing: clark_kent and superman
Superman flies.
  reading 3 of 3
  tell   _fly_v_1(e1, superman)
  stored, 1 new fact(s)
Does Clark Kent fly?
  reading 1 of 5
  ask    _fly_v_1(E, clark_kent)
  Yes
  fly(clark_kent)  (told: "Superman flies.")
Is the robin happy?
  reading 1 of 5
  ask    _robin_n_1(tweety), _happy_a_with(E, tweety)
  Yes
  tweety is a robin  (told: "Tweety is a robin.")
  happy(tweety)  (by rule 4)
    tweety is a robin  (told: "Tweety is a robin.")
    sing(tweety)  (told: "Tweety sings.")
The dog barks.
  reading 1 of 2
  refuse DEFINITE_MATCHES: 2 known things match
  refused
Tweety does not fly.
  reading 1 of 4
  tell   not _fly_v_1(_, tweety)
  refused, contradicts:
  fly(tweety)  (by rule 2)
    tweety is a bird  (by rule 1)
      tweety is a robin  (told: "Tweety is a robin.")
```

## Phase 5: modifiers and time (tier C)

Built `rules/modifiers.py`: a locative preposition attaches to the event it modifies (its own event argument is not used). `loc_nonsp` in a question becomes the pattern `_*_p_loc`, which matches any locative preposition by its sense suffix. Tense: `tense(e, past)` for a told past event, not reasoned over.

Also changed in this phase, from the fixtures: reading overlap now counts predicate and arity together. Without arity, "Where does Kim live?" took the three-place reading of "live", and the store matched it on name alone.

Checks, exact output:

```
$ .venv/bin/pytest -q tests/test_dialogue_c.py
(count superseded: see the latest entry)
$ .venv/bin/pytest -q
(count superseded: see the latest entry)
```

The tier C dialogue through the repl:

```
Kim lives in Oslo.
  reading 1 of 4
  tell   _live_v_1(e1, kim)
tell   _in_p_loc(e1, oslo)
  stored, 2 new fact(s)
Sandy arrived.
  reading 1 of 1
  tell   _arrive_v_1(e1, sandy)
tell   tense(e1, past)
  stored, 2 new fact(s)
Who lives in Oslo?
  reading 1 of 2
  ask X  _live_v_1(E, X), _in_p_loc(E, oslo)
  Kim
live(kim)  (told: "Kim lives in Oslo.")
in(oslo)  (told: "Kim lives in Oslo.")
Where does Kim live?
  reading 1 of 2
  ask X  _*_p_loc(E, X), _live_v_1(E, kim)
  Oslo
in(oslo)  (told: "Kim lives in Oslo.")
live(kim)  (told: "Kim lives in Oslo.")
Does Kim live in Oslo?
  reading 2 of 5
  ask    _live_v_1(E, kim), _in_p_loc(E, oslo)
  Yes
live(kim)  (told: "Kim lives in Oslo.")
in(oslo)  (told: "Kim lives in Oslo.")
Does Kim live in Bergen?
  reading 2 of 5
  ask    _live_v_1(E, kim), _in_p_loc(E, bergen)
  Unknown
```

## Phase 6: suppositions

Built: `Mind.suppose(text)` stores a statement in a new context (`s1`, `s2`, ...) that inherits `world`. The engine derives inside that context, questions asked in it see both, and `Mind.drop()` removes the context's facts, their why and conflict rows, and the fresh entities nothing else uses.

Resolution recorded in PLAN.md: the test tells "No penguin flies." in world first, because the tier B table never tells it, so suppose "Tweety is a penguin." has a negative consequence to conflict with.

Checks, exact output:

```
$ .venv/bin/pytest -q tests/test_suppose.py
(count superseded: see the latest entry)
$ .venv/bin/pytest -q
(count superseded: see the latest entry)
```

Acceptance as stated in SPEC.md: inside the supposition, "Does Tweety fly?" is Conflict; outside it is Yes; after drop, the fact count equals the count before (`test_supposed_penguin_makes_tweety_conflict_inside_only`).

## Phase 7: widening coverage

Built `scripts/coverage.py`. It takes sentence files, compiles each sentence in an empty store (lookup included), and reports the share compiled and the refusals by code and detail, most frequent first. `scripts/record.py` takes sentence files too.

`tests/extra.txt` was written before any coverage result was seen.

Before any change, on the sentences of `sentences.txt` plus `extra.txt`:

```
(coverage superseded: see the latest entry)
   8  DEFINITE_MATCHES  0 known things match
   1  UNSUPPORTED_PREDICATE  card
```

Review of every compiled form in `extra.txt` found wrong meanings, which the spec counts as failures. Fixed before the first round, with regression tests in `tests/test_widening.py`:

- `No teacher is a student.` compiled to a positive rule. Negation now reaches a copula complement and a `no` head.
- `Milo is not a cat.` compiled to `cat(milo)`, with the negation dropped. Same cause.
- A bare plural in object position ("Every car needs fuel.", "Ben teaches math.") was a universal. Only a statement's subject is universal now; any other bare plural is an indefinite.
- `studies hard` made a new event for the adverb. An adverb or preposition now attaches to the event it modifies.
- The where-pattern matched only locations, so "Where does Sam work?" missed `in Paris`, a state. It now matches `_*_p_[ls]*`.

Round 1. Most frequent refusal: `DEFINITE_MATCHES 0 known things match` (8). Three new sentences recorded in `tests/round1.txt`: "The teacher is tired.", "The cup is empty.", "Is the cat asleep?". Each is refused on an empty store, which is correct because no referent is known. A definite does compile once its referent is told: "Anna reads a book." then "The book is old." (tested in `test_widening.py`). Decision: leave as is. No rule added.

Round 2. Most frequent refusal now `UNSUPPORTED_PREDICATE card` (1 before round 1; 4 after it). Three new sentences recorded in `tests/round2.txt`: "Ana owns two cats.", "Tom has four books.", "Every bike has three wheels.". Counting is out of scope in SPEC.md, so these stay refused. Decision: leave refused. No rule added.

Coverage after round 1 and round 2 (the rounds add sentences and add no rule):

```
(coverage superseded: see the latest entry)
  11  DEFINITE_MATCHES  0 known things match
   1  UNSUPPORTED_PREDICATE  card
(coverage superseded: see the latest entry)
  11  DEFINITE_MATCHES  0 known things match
   4  UNSUPPORTED_PREDICATE  card
```

Checks, exact output:

```
$ .venv/bin/pytest -q tests/test_widening.py
(count superseded: see the latest entry)
$ .venv/bin/pytest -q
(count superseded: see the latest entry)
```

## Phase 8: proposing rules

Built `Mind.propose()` and `Mind.confirm(p)`. A proposal is a pair of one-place predicates P and Q (noun, or adjective with its thing argument) where at least three known things have P, every one of them has Q, Q has a thing P lacks, and no stored rule already links P to Q. The question is "Is every P a Q?". `confirm` stores the rule, with the confirmed question as its sentence. Nothing is stored before confirm.

The spec's acceptance needs "four things sharing two predicates" to give exactly one proposal. Two predicates with the same extension would propose each other, so the "Q has a thing P lacks" condition is what makes the count one. Recorded in DECISIONS.md.

Checks, exact output:

```
$ .venv/bin/pytest -q tests/test_propose.py
(count superseded: see the latest entry)
$ .venv/bin/pytest -q
(count superseded: see the latest entry)
```

## Summary

What passes: all of SPEC.md's acceptance checks, phases 0 to 8. The test suite covers the tier A and B dialogues and tier C, the printed forms of tier A and tier C sentences, the 50,000-fact fixpoint, suppositions, proposals, and the phase 7 regression set. `scripts/repl.py` prints the reading number, the printed form and the result for each input.

What is refused, and why:

- `DEFINITE_MATCHES 0 known things match`. A definite with no known referent in the store. Correct: it compiles once a referent is told (tested in `test_widening.py`).
- `UNSUPPORTED_PREDICATE card` (4). Counting and numbers, which SPEC.md puts out of scope.
- Rules and identity inside a supposition, refused with a message. The store cannot drop them cleanly yet (Open).

Coverage, from `scripts/coverage.py` over `tests/sentences.txt`, `tests/extra.txt`, `tests/round1.txt` and `tests/round2.txt`, exact output:

```
(coverage superseded: see the latest entry)
  11  DEFINITE_MATCHES  0 known things match
   4  UNSUPPORTED_PREDICATE  card
```

Spec points resolved myself (each is in DECISIONS.md or the resolutions at the top of PLAN.md): phase 6's conflict needs "No penguin flies." told first; conflict rows cover a clash once one side is derived; one INSERT per head atom; a lemma scan that exempts the grammar's function words; the reading choice counts only eventive readings and matches on predicate and arity; the store renames fresh constants; repeated statements add nothing per context; bare plurals are universal only as subject; "where" matches any locative or state preposition; the copula's identity keeps the older entity; propose needs a counterexample direction.

## Open

- Rules and identity merges inside a supposition are refused. The rule and merge tables have no context column, so `drop` cannot remove them yet.
- Negation as failure is evaluated round by round. The stratification check is the spec's; a strata-by-strata evaluation is not built.
- Parser senses: "Jo writes letters." reads `write_v_to`, and "Every pilot flies a plane." reads `fly_v_to`. The reading choice does not rank senses, so these stay as parsed.
- A repeated statement adds nothing only when its text is identical. Two wordings of one meaning add facts.
- Definite referents that are anonymous (`a1`) are recorded with kind `named`.
- The lemma scan covers the lemmas of `tests/sentences.txt`, as the spec says. Extra sentences are not scanned.
- `propose` returns the thing ids as support. Showing their wording would reuse `say.fact_text`, not done.
- SQUID and libglot: not used. SQUID is named in SPEC.md, and its code was not read. The only idea taken is keeping the parser session open, recorded in DECISIONS.md.

## Phase 9: debts from the review (SPEC2)

Eight items, one commit each: 7bec894 records, e27ee02 split of compile.py (test output identical before and after), b5a3bdd consumption of scopal predicates, 3676cfd refusal table, 729b711 reading choice, 01c59f7 stratified negation, ffb1fb9 repeats by meaning, 3405a53 preposition widening and the repl. The four unresolved findings in REVIEW.md are marked fixed with these commits.

```
$ .venv/bin/pytest -q
241 passed in 8.72s
$ .venv/bin/python scripts/coverage.py tests/sentences.txt tests/extra.txt tests/round1.txt tests/round2.txt
compiled 71 of 86 (82.6%)
```

Open: "Where is Bob?" after "Bob is in Paris." is Unknown (argument shapes differ); "Ivy sings in Turin." stores a rule about ivy (the parser reads the name as a mass noun). Both in DECISIONS.md.

## Phase 10: describing a thing

Built Describe(entity), rules/describe.py, store.mentioning, Mind._describe. Ten own-word sentences in tests/own.txt, expectations in tests/test_phase10.py (written before the code). Three earlier tests that used 'Who is Kim?' as the unconstrained-wanted example now use 'Who is who?'; SPEC2 changes that result.

```
$ .venv/bin/pytest -q
254 passed in 8.85s
```

## Phase 11: conditionals

Rules for 'If A, B.' and 'B if A.'; ten own-word cases in tests/test_phase11.py. Found and fixed on the way: a rule body of only a negated atom crashed the engine (SQL lost its conditions) and left the rule stored; each hear is now one transaction. The grammar's unknown fallback is a reading refusal.

```
$ .venv/bin/pytest -q
276 passed in 9.72s
```

## Phase 12: negation over nouns, negated questions

The statement half was verified against the dialogue, not rebuilt. Negated questions invert Yes and No; absence stays Unknown. Three earlier tests that expected NEGATED_QUESTION were updated to the new behaviour (SPEC2 lifts that refusal).

```
$ .venv/bin/pytest -q
290 passed in 10.43s
```

## Phase 13: pronouns

Built rules/pronouns.py, the mention table, notes on logical forms, 'you'/'I' wording. Dialogue and ten own-word cases in tests/test_phase13.py. SPEC2 changes 'She swims.' from UNSUPPORTED_PREDICATE to NO_ANTECEDENT; the refusal test uses 'Kim can sing.' for the former.

```
$ .venv/bin/pytest -q
312 passed in 10.15s
```

## Phase 14: numbers

Cardinals in statements, How many, at-least questions. Dialogue and ten own-word cases in tests/test_phase14.py. SPEC2 changes two earlier refusal tests (Ana owns two cats; Ada keeps two cats).

```
$ .venv/bin/pytest -q
337 passed in 10.26s
```

## Phase 15: coordination

And distributes over names, noun phrases and verb phrases; or is accepted in questions only. Ten or more own-word cases in tests/test_phase15.py. SPEC2 changes the earlier refusals of 'and'; the COORDINATION test now uses 'or' in a statement.

```
$ .venv/bin/pytest -q
375 passed in 11.25s
```

### Phase 16, what the grammar does with unknown words (found from fixtures)

Fixtures: `tests/fixtures/tweety_is_a_blorp.json`, `every_blorp_flibbers.json`, `tweety_is_glorpy.json`, `does_tweety_flibber.json`. A noun is `_blorp/nn_u_unknown`, an adjective `_glorpy/jj_u_unknown`, a verb `_glorbs/vbz_u_unknown`; the lemma is the surface form and the tag is a guess. "Every blorp flibbers." has no reading at all (open: listed in `tests/test_fixtures.py` as an expected failure). Questions with an unknown verb parse only as nonsense.

## Phase 16: unknown words

Unknown nouns, adjectives and verbs in statements are treated like known predicates; unknown verbs in questions and two unknown words are refused by name or have no reading. Ten own-word cases in tests/test_phase16.py. The result is a hybrid of the two accepted outcomes, explained in DECISIONS.md. One regression from phase 9 fixed (UNCONSTRAINED_WANTED is a reading refusal).

```
$ .venv/bin/pytest -q
389 passed, 1 xfailed in 11.63s
```

## Phase 17: a public interface

tolk/__init__.py exposes exactly read, printed, Mind and the logical form types. Ten own-word cases in tests/test_phase17.py.

```
$ .venv/bin/pytest -q
404 passed, 1 xfailed in 12.24s
```

## Checkpoint after phase 17

Reread everything changed since the review (commits 7bec894 to 332c91d), reran the tier A, B and C dialogues through the repl (every result as in SPEC.md), and ran an automated pass for unused imports and definitions. Removed: two unused imports, the second home of the unknown-word predicate shape (now `lf.UNKNOWN_PRED`). Found and fixed on the way: an unknown verb was widened as if it were an adjective.

```
$ .venv/bin/pytest -q
405 passed, 1 xfailed in 11.91s
```

Fragile, in order of how likely each is to bite:

1. Making `UNSUPPORTED_PREDICATE` final means a reading ranked first that uses a scopal verb ends the search even when a later reading is the sentence. Seen once: "If Kim does not own a dog, Kim is tired." (the first reading takes `tire` as a verb).
2. `compile_reading` is about 170 lines of interacting cases (scope, polarity, cardinals, groups, conditionals) in a file of 256 lines. The next feature that needs another special case will need the function split first.
3. Unknown words depend on the grammar's tagger guessing: an adjective can come back as a noun in a question, and two unknown words in one sentence give no reading. The matching widens noun and adjective only.
4. Pronouns: questions leave no mentions, a thing made by an indefinite counts as a mention (so "Kim owns a dog. It barks." is ambiguous), a group made by a cardinal is not a mention, and there is no plural pronoun until a plural thing exists.
5. A distributed "and" shares one event across the copies in a statement; collective readings are ignored.
6. "How many" counts the known things; zero means none known, not none.
7. The lemma scan reads comments too. A comment that uses a word from any sentence in `sentences.txt` fails the test. Twelve comments have been reworded for it so far.
8. Open from phase 9: "Where is Bob?" after "Bob is in Paris." is Unknown (argument shapes differ); "Ivy sings in Turin." stores a rule about ivy (the parser reads the name as a mass noun).

## Phase 18: defaults and the conflict policy

Defaults, strength levels, defeat and the specific/trusted/recent policy; universal questions answered by a scratch derivation. The dialogue and ten own-word cases are in tests/test_phase18.py. Earlier results changed as SPEC2 says: Birds are animals is now a default (its answers are unchanged); universal and negated bare-noun questions are answered, not refused.

```
$ .venv/bin/pytest -q
423 passed, 1 xfailed in 13.94s
```

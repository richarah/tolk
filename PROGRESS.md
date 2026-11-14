# PROGRESS

## Phase 0: parser and fixtures

Checks run:

```
$ .venv/bin/pytest -q
........................................................................ [ 90%]
........                                                                 [100%]
80 passed in 0.10s
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
2 reading(s): Tweety is a robin.
2 reading(s): Every robin is a bird.
2 reading(s): Every bird flies.
1 reading(s): Birds are animals.
1 reading(s): Tweety sings.
5 reading(s): Every robin that sings is happy.
1 reading(s): Kim is a person.
1 reading(s): Kim owns a dog.
1 reading(s): Every person who owns a dog is happy.
1 reading(s): Kim likes Sandy.
1 reading(s): Rex is a dog.
1 reading(s): Every dog has an owner.
5 reading(s): Does Tweety fly?
5 reading(s): Is Tweety a bird?
5 reading(s): Is Tweety an animal?
5 reading(s): Is Tweety happy?
3 reading(s): What flies?
2 reading(s): Which robin sings?
1 reading(s): Who is happy?
1 reading(s): Who likes Sandy?
2 reading(s): Who does Kim like?
5 reading(s): Is Sandy happy?
2 reading(s): Does Rex have an owner?
1 reading(s): Pingu is a penguin.
4 reading(s): Pingu does not fly.
5 reading(s): No penguin flies.
1 reading(s): Every penguin is a bird.
1 reading(s): Clark Kent is Superman.
3 reading(s): Superman flies.
5 reading(s): Does Pingu fly?
5 reading(s): Does Clark Kent fly?
5 reading(s): Is the robin happy?
2 reading(s): The dog barks.
4 reading(s): Tweety does not fly.
4 reading(s): Kim lives in Oslo.
1 reading(s): Sandy arrived.
2 reading(s): Who lives in Oslo?
2 reading(s): Where does Kim live?
5 reading(s): Does Kim live in Oslo?
5 reading(s): Does Kim live in Bergen?
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
28 passed in 0.06s
$ .venv/bin/pytest -q
108 passed in 0.15s
```

All 23 tier A sentences compile to the expected printed form (table at the top of `tests/test_compile.py`). The lemma scan passes after the function-word exemption described in DECISIONS.md.

## Phase 2: store and engine

Built `tolk/store.py` and `tolk/engine.py`. The engine compiles each rule to SQL, one `INSERT OR IGNORE ... SELECT` per head atom plus one skolem `entity` insert per created variable and one `why` insert per head atom. Every value is a bound parameter. Rounds are semi-naive as the spec describes.

Checks, exact output:

```
$ .venv/bin/pytest -q -s tests/test_engine.py
fixpoint: 300000 derived facts in 1.29s
5 passed in 2.71s
$ .venv/bin/pytest -q
1 failed, 112 passed in 2.97s
```

The 50,000-fact timing is the `fixpoint` line above (300,000 facts derived through six rules).

## Phase 3: questions, proofs, wording, repl

Built `tolk/ask.py`, `tolk/say.py`, `tolk/mind.py`, `scripts/repl.py`. `ask.py` reuses `engine.Match`, the FROM/WHERE generator that rules also use. `say.py` is stiff: facts show as predicate and arguments; the article is chosen from the lemma.

Checks, exact output:

```
$ .venv/bin/pytest -q
126 passed in 3.63s
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
14 passed in 0.42s
$ .venv/bin/pytest -q
140 passed in 5.47s
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
5 passed in 0.20s
$ .venv/bin/pytest -q
149 passed in 5.58s
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

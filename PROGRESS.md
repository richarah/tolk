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

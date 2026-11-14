# SPEC: tolk

A system that reads English statements, stores what they say with its source, reasons over the store, and answers questions with proofs. Nothing neural or statistical runs at runtime. Every step can be inspected.

"tolk" is a placeholder name. Rename the package if told to.

## How to use this file

You are a coding agent working in this directory. In each session:

1. Read this whole file, then `PROGRESS.md` and `DECISIONS.md` if they exist.
2. Do the next unfinished phase, and only that phase.
3. Run its acceptance checks. When they pass, append a dated entry to `PROGRESS.md` (what was built, the exact command output of the checks, anything left open) and stop.
4. If you cannot make the checks pass, stop and write what blocks you in `PROGRESS.md`. Do not move on, and do not change the checks.

Where this file is silent, choose the smaller option and record the choice in `DECISIONS.md` in one or two lines.

## Hard rules

These apply in every phase. Breaking one is a failed phase even if tests pass.

**Truth of the data**

1. Never write a semantic structure (MRS) by hand, from memory, or by guessing. Every fixture is recorded from a real run of the parser by `scripts/record.py`. If the parser is not working, stop.
2. Before writing any rule for a construction, open the recorded fixture for a sentence that uses it and read it. Argument order, predicate names and variable properties come from the fixture, never from this file or from memory. Predicate names quoted in this file are illustrations and may differ from the grammar's real output.
3. No rule, in any file under `tolk/`, may mention a content word. Rules key on a quantifier name, an abstract predicate name (one with no leading underscore, such as `neg` or `named`), a part of speech, or an argument pattern. A rule that mentions `robin`, `fly` or any other lemma is cheating on the tests.
4. Numbers in any document (coverage, timings, accuracy) are pasted from the output of a script in this repository. Never estimate one.

**Behaviour**

5. An input the system cannot represent exactly is refused with a reason. It is never partly stored, guessed at, or silently dropped. A refusal is a normal return value, not an exception.
6. No statistical or neural component, and no network call, at runtime. The setup script may download.
7. SQL uses fixed identifiers and bound parameters only. Never build SQL by inserting a value into a string.

**Code**

8. Dependencies: Python 3.11 or later, `pydelphin`, `pytest`, and the standard library (including `sqlite3`). Nothing else without an entry in `DECISIONS.md` that says what it replaces and why.
9. Keep it small. No module over 300 lines. No abstract base classes, plugin systems, registries, config files, logging frameworks, CLI frameworks, async code or caches. Use a function unless state forces a class.
10. No `try`/`except` that hides an error. Catch only what you handle, and name the exception type.
11. Tests use recorded fixtures or the real parser. No mocks of the parser or the store.
12. Never delete, skip, loosen or rewrite a test to make it pass. If a test in this file is wrong, say why in `PROGRESS.md` and stop.
13. Comments say why, not what. No banner comments, no docstrings that restate the signature, no emojis, no README beyond the short one in phase 0.
14. Public functions have type hints. Logical-form types are frozen dataclasses.
15. Do not add features this file does not ask for. If something seems missing, write it under "Open" in `PROGRESS.md`.

## Layout

```
pyproject.toml
README.md              ten lines at most: what it is, how to set up, how to run the repl
SPEC.md                this file
PROGRESS.md
DECISIONS.md
scripts/
  setup_erg.sh         downloads the parser and grammar into ./erg/
  record.py            sentences.txt -> tests/fixtures/*.json
  coverage.py          how many sentences compile, and why the rest are refused
  repl.py              talk to it
tolk/
  erg.py               parser session: text -> list of readings
  sem.py               neutral view of one reading
  lf.py                logical form types and their printed form
  compile.py           reading -> logical form, or a refusal
  rules/               one file per construction family, added as phases need them
  store.py             schema, writing, identity
  engine.py            rules -> SQL, run to fixpoint
  ask.py               questions, answers, proofs
  say.py               wording of facts and proofs
  mind.py              tell(text) and ask(text): the loop that ties it together
tests/
  sentences.txt        one sentence per line, grouped by tier with comment lines
  fixtures/            one JSON file per sentence, written only by record.py
  test_*.py
```

## Components

- Parser: ACE 0.9.34 with the English Resource Grammar 2018 image.
  - `http://sweaglesw.org/linguistics/ace/download/ace-0.9.34-x86-64.tar.gz`
  - `http://sweaglesw.org/linguistics/ace/download/erg-2018-x86-64-0.9.34.dat.bz2`
  - Linux x86-64 only. The parser's own home page is `http://sweaglesw.org/linguistics/ace/` if a link has moved.
- PyDelphin (`delphin.ace`, `delphin.mrs`, `delphin.codecs.simplemrs`) drives the parser and reads its output.
- SQLite through the standard library is the store.

## Related repositories (for awareness only)

The owner of this project has two related repositories. They are listed so you know they exist. Nothing in this spec requires them, and no phase is easier or more correct for using them.

- `https://github.com/richarah/squid`: English questions to SQL, using the same parser and grammar. Useful to read for how it keeps a parser session open and how it injects vocabulary into the grammar.
- `https://github.com/richarah/libglot`: a C++ parser and generator framework with an SQL implementation. Not relevant to any phase here. It matters only to a later port.

Rules for both:

- Do not add either as a dependency, vendor their code, or shape this project's layout or naming to match theirs.
- You may read them. If you take an idea, say which one in `DECISIONS.md`. Do not copy code you have not run.
- Do not edit them, open issues on them, or plan work in them.
- If you think one of them should be used after all, write the case under "Open" in `PROGRESS.md` and carry on without it.

## Concepts

### Reading

The parser returns up to 5 readings per sentence. `sem.py` turns each into a plain structure:

- `index`: the main event variable.
- `eps`: a list of predications, each with `pred`, `label` and `args` (a dict such as `ARG0`, `ARG1`, `RSTR`, `CARG`).
- `qeq`: a dict from a hole to the label it is equal to modulo quantifiers.
- `props`: a dict from variable to its properties (for example sentence force, tense, number).

A quantifier's restriction is the set of predications whose label is `qeq[RSTR]`. Do not skip that indirection.

### Logical form

A reading compiles to exactly one of:

- `Tell(atoms)`: ground facts to store.
- `Rule(head, body)`: for every binding that satisfies the body, the head holds.
- `Ask(body, wanted)`: `wanted` is a tuple of variables. Empty means yes or no.
- `Same(a, b)`: two names for one thing.
- `Refusal(code, detail)`.

Terms are `Const(id)` or `Var(name)`. An atom is `Atom(pred, args, positive=True)`.

Atoms mirror the grammar's predications. This is the central design choice, and it keeps the rule set small:

- A noun predication becomes `pred(x)`, or `pred(x, y)` when the noun has a complement.
- A verb, adjective or preposition predication keeps its event: `pred(e, a1)`, `pred(e, a1, a2)`. A modifier of an event takes that event as an argument, so "lives in Oslo" is two atoms that share `e`.
- Unexpressed arguments are dropped from the end. An unexpressed argument before an expressed one is a refusal.
- `pred` is the grammar's predicate string, unchanged.

Printed form, used in tests and shown to the user before anything is stored:

```
tell   _robin_n_1(tweety)
tell   _sing_v_1(e1, tweety)
rule   _fly_v_1(E!, X) :- _bird_n_1(X)
rule   _happy_a_with(E!, X) :- _robin_n_1(X), _sing_v_1(E1, X)
ask    _fly_v_1(E, tweety)
ask X  _like_v_1(E, X, sandy)
same   clark_kent = superman
refuse NEGATION_IN_RULE_HEAD: ...
```

`E!` in a head marks a thing the rule creates (see Skolem terms). Variables print as `X`, `Y`, `Z` for things and `E`, `E1`, `E2` for events, in order of first appearance.

### Mapping rules, by family

- Names: `named` with its `CARG` gives a constant. Two names joined by `compound` are one constant.
- "is a": the copula with an indefinite complement adds the complement's atoms to the subject. It creates no new thing.
- "is" between two definite things: `Same`.
- Universal quantifiers, and a bare plural subject of a statement: `Rule`. The body is everything inside the restriction, including the restrictions of indefinites that appear there. The head is the rest.
- Indefinites in a statement: a new constant. In a rule body or a question: a variable. In a rule head: a Skolem term.
- Definites: must match exactly one known thing, otherwise a refusal that says how many matched.
- Which, who, what: a wanted variable.
- Sentence force comes from the properties of `index`. Statement and question only. Anything else is a refusal.
- Any predication no rule covers: `Refusal("UNSUPPORTED_PREDICATE", pred)`.

### Choosing a reading

Compile every reading. Among those that are not refusals, pick the one whose predicates overlap most with predicates already in the store. Break ties by the parser's order. Report which reading was chosen and how many there were. If all are refusals, return the first reading's refusal.

### Store

SQLite tables:

- `sentence(id, text)`
- `entity(id, kind)` where kind is `named`, `anon`, `event` or `skolem`
- `name(entity, text)`
- `fact(id, pred, a0, a1, a2, positive, ctx, round)` unique on all but `id` and `round`. Unused argument columns hold the empty string.
- `why(fact, sentence, rule, premises)` where exactly one of `sentence` and `rule` is set and `premises` is a JSON list of fact ids.
- `rule(id, sentence, printed)`
- `merge(kept, dropped, sentence)`
- `conflict(positive_fact, negative_fact)`

Events told in statements get fresh constants (`e1`, `e2`). `ctx` is `world` until phase 6.

### Engine

- A rule compiles to one `INSERT ... SELECT` over self-joins of `fact`, with `NOT EXISTS` for negated body atoms.
- Semi-naive: after the first run of a rule, each run requires at least one body atom from the previous round.
- Run all rules until a round adds nothing.
- Every derived fact gets a `why` row with the rule and the premise fact ids.
- Skolem terms: a thing created by a rule head has the id `sk:<rule id>:<creating variable>:<the body bindings joined by commas>`, so the same bindings always give the same thing. A rule does not fire when one of its bindings is itself a Skolem term made by the same rule. That guard is what guarantees termination.
- Negated body atoms must not depend on the rule's own head predicate, directly or through other rules. Refuse the rule otherwise.

### Answers

Four values: `Yes`, `No`, `Unknown`, `Conflict`.

- `Yes`: a positive fact matches.
- `No`: only a stored negative fact matches. Absence of a fact is `Unknown`, never `No`.
- `Conflict`: both match. Show both proofs.

A proof is a tree: each fact with either the sentence that stated it or the rule's sentence and the proofs of its premises.

## Phases

### Phase 0: parser and fixtures

Build `scripts/setup_erg.sh`, `tolk/erg.py`, `tolk/sem.py`, `scripts/record.py`, `pyproject.toml`, the short README, and `tests/sentences.txt` with the tiers below.

`record.py` parses every line of `sentences.txt` with up to 5 readings and writes one fixture per sentence: the text, and for each reading the raw SimpleMRS string and the neutral structure.

Acceptance:

- `pytest` passes a test that every sentence has a fixture with at least one reading. A sentence with no reading is listed in `PROGRESS.md` under "Open", and its test is marked as an expected failure with that reason. This is the only permitted use of expected failure.
- `PROGRESS.md` contains the full first reading of three fixtures, pasted. Read them before phase 1.

### Phase 1: logical form and the core mapping

Build `lf.py`, `compile.py` and the rule families for tier A. Tests compare the printed form of the chosen reading of each tier A sentence with an expected string.

Write the expected strings yourself from the shapes in "Printed form" and the predicate names in the fixtures. Put them in one table at the top of the test file so a person can review them.

Acceptance: all tier A sentences compile to the expected printed form. A test scans `tolk/` and fails if any lemma from `sentences.txt` appears in the source.

### Phase 2: store and engine

Build `store.py` and `engine.py`.

Acceptance, as tests:

- Telling the tier A statements in order yields the derived facts listed under "Tier A dialogue".
- Telling the same statement twice adds nothing the second time.
- "Every dog has an owner." with one dog creates one owner. Running the engine again creates none.
- A rule set that would recurse through its own Skolem terms stops.
- 50,000 facts under a chain of 6 rules reach fixpoint. Paste the timing into `PROGRESS.md`.

### Phase 3: questions, proofs, wording, repl

Build `ask.py`, `say.py`, `mind.py`, `scripts/repl.py`.

`say.py` words a fact from its predicate's part of speech with plain templates. It is allowed to be stiff. It is not allowed to be wrong.

Acceptance: the tier A dialogue below, run through `mind.py`, gives the stated answers, and each `Yes` carries a proof whose leaves are told sentences. The repl prints, for every input, the chosen reading number, the printed logical form, and the result.

### Phase 4: negation, "no", identity, definites

- `neg` over a clause in a statement: a negative fact. It has no event, so its event column is empty.
- `neg` in a rule body: negation as failure.
- `neg` or "no" in a rule conclusion: the rule derives negative facts.
- Telling a fact whose opposite is stored or derived: refuse, and show the proof of the opposite.
- A derived fact whose opposite is also derived: keep both, and add a `conflict` row.
- `Same`: keep the older entity, rewrite the other's facts onto it, record the merge, rerun the engine.

Acceptance: the tier B dialogue.

### Phase 5: modifiers and time

- Prepositions and adverbs that modify an event become atoms on that event.
- "Where" questions.
- Tense is stored as a fact about the event (`tense(e, past)`) and is not reasoned over.

Acceptance: the tier C dialogue.

### Phase 6: suppositions

`mind.suppose(text)` stores a statement in a new context that inherits `world`. The engine derives inside it. Questions asked in that context see both. Dropping the context removes everything in it and nothing else.

Acceptance: suppose "Tweety is a penguin." after tier B. Inside the supposition, "Does Tweety fly?" is `Conflict`. Outside, it is still `Yes`. After dropping it, the fact count equals the count before.

### Phase 7: widening coverage

Build `scripts/coverage.py`: for every sentence in `sentences.txt` and in any extra file given as an argument, report the share that compile and a count of refusals by code and predicate, most frequent first.

Then repeat, at most five times per session:

1. Take the most frequent refusal.
2. Record fixtures for three new sentences that show it, and read them.
3. Decide what it means in the store. Write the decision in `DECISIONS.md` in a few lines before writing code.
4. Add the rule, the tests, and the sentences.
5. Rerun coverage and paste the before and after lines into `PROGRESS.md`.

If a construction has no exact meaning in this store, leave it refused and say so.

### Phase 8: proposing rules

`mind.propose()` looks for a pair of one-place noun or adjective predicates P and Q where at least three known things have P, all of them have Q, and no rule already derives Q from P. It returns the candidate as an English question ("Is every robin a bird?") with the supporting facts. Nothing is stored unless the user confirms. A confirmed rule is stored with the confirmation as its source.

Acceptance: a test with four things that share two predicates yields exactly one proposal. With a counterexample it yields none.

## Out of scope

Do not start any of these: pronouns, numbers and counting, comparatives, generating English through the grammar, importing outside knowledge, defaults where a specific rule overrides a general one, a C++ port, a GPU path, a web interface, or integration with SQUID.

## Sentences

### Tier A

```
Tweety is a robin.
Every robin is a bird.
Every bird flies.
Birds are animals.
Tweety sings.
Every robin that sings is happy.
Kim is a person.
Kim owns a dog.
Every person who owns a dog is happy.
Kim likes Sandy.
Rex is a dog.
Every dog has an owner.
Does Tweety fly?
Is Tweety a bird?
Is Tweety an animal?
Is Tweety happy?
What flies?
Which robin sings?
Who is happy?
Who likes Sandy?
Who does Kim like?
Is Sandy happy?
Does Rex have an owner?
```

### Tier A dialogue

Tell the twelve statements in order, then ask:

| Question | Answer |
|---|---|
| Does Tweety fly? | Yes, in three steps: robin, bird, flies |
| Is Tweety an animal? | Yes |
| Is Tweety happy? | Yes |
| What flies? | Tweety |
| Which robin sings? | Tweety |
| Who is happy? | Kim and Tweety |
| Who likes Sandy? | Kim |
| Who does Kim like? | Sandy |
| Is Sandy happy? | Unknown |
| Does Rex have an owner? | Yes |

### Tier B

```
Pingu is a penguin.
Pingu does not fly.
No penguin flies.
Every penguin is a bird.
Clark Kent is Superman.
Superman flies.
Does Pingu fly?
Does Clark Kent fly?
Is the robin happy?
The dog barks.
Tweety does not fly.
```

### Tier B dialogue

Continue from tier A.

| Input | Result |
|---|---|
| Pingu is a penguin. | stored |
| Pingu does not fly. | stored as a negative fact |
| Does Pingu fly? | No |
| Every penguin is a bird. | stored. Pingu now also derives "flies", so a conflict is recorded |
| Does Pingu fly? | Conflict, with both proofs |
| Clark Kent is Superman. | stored as one thing with two names |
| Superman flies. | stored |
| Does Clark Kent fly? | Yes |
| Is the robin happy? | Yes (one robin is known) |
| The dog barks. | refused: two dogs are known |
| Tweety does not fly. | refused: contradicts a derived fact, proof shown |

### Tier C

```
Kim lives in Oslo.
Sandy arrived.
Who lives in Oslo?
Where does Kim live?
Does Kim live in Oslo?
Does Kim live in Bergen?
```

### Tier C dialogue

| Input | Result |
|---|---|
| Who lives in Oslo? | Kim |
| Where does Kim live? | Oslo |
| Does Kim live in Oslo? | Yes |
| Does Kim live in Bergen? | Unknown |
| Sandy arrived. | stored, with a past tense fact on the event |

# SPEC2: wider language, a deeper engine, and SQUID on top

This extends `SPEC.md`. Every hard rule, concept and convention there still applies. Where the two disagree, this file wins, and you note the difference in `DECISIONS.md`.

Three parts, in order:

- Part A (phases 9 to 17): wider language in tolk.
- Part B (phases 18 to 24): defaults, revision, time, beliefs, comparatives, morphology, generation.
- Part C (phases 25 and 26): SQUID uses tolk as its front end.

## How to work

- One session, all phases in order. Continue when a phase's acceptance checks pass.
- For each phase: add its sentences to `tests/sentences.txt`, record fixtures, read them, write the plan for that phase into `PLAN.md`, then build. No rule before its fixtures have been read.
- After each phase: run the whole test suite, paste the exact output into `PROGRESS.md`, commit.
- Each phase also gets ten sentences of your own with the same constructions and different words. Record them, write the expected result before running, and add them to the suite. If one fails, fix the rule family, never the sentence.
- Every dialogue in `SPEC.md` and in this file is a permanent test. A later phase may not change an earlier dialogue's result unless this file says so.
- Checkpoints: after phase 17 and after phase 24, stop building and review. Reread everything changed since the last checkpoint, rerun every dialogue, remove what is unused or duplicated, and write a short "Checkpoint" entry in `PROGRESS.md` listing anything fragile. Then continue.
- Stop only if the parser gives no usable reading for a phase's sentences, a check cannot be met without breaking a hard rule, or the same check has failed three times after three different fixes. Write what blocks you and stop.

The decisions below are already made. Do not reopen them. Record anything else you decide.

## Settings

There are no config files. Settings are arguments to `Mind(...)`, stored in a `meta(key, value)` table in the store so that a store always knows how it was derived. Changing a setting rebuilds the derived facts. `scripts/repl.py`, and only it, reads these environment variables and passes them on:

- `TOLK_POLICY`: comma-separated, from `specific`, `trusted`, `recent`. Default `specific`. See phase 18.
- `TOLK_AUTO_REVISE`: `0` or `1`. Default `0`. See phase 19.

## Part A: language

### Phase 9: debts from the review

Read `REVIEW.md` first. Do these eight items in this order. An item is done when its own test passes and every existing test still passes. Commit after each.

1. **Records.** `PROGRESS.md` has stale counts. Replace every number in it with fresh script output, or delete the number.

2. **Split `compile.py`.** Move each rule family into its own file under `tolk/rules/`. `compile.py` keeps only reading choice and dispatch. This step changes no behaviour: the test output before and after must be identical. No file over 300 lines.

3. **Full consumption check.** Every predication in a reading must be consumed by some rule: it becomes an atom, a term, a quantifier role or a property. Any predication left over makes that reading a refusal with `UNSUPPORTED_PREDICATE` and the predicate's name. This replaces the narrower checks on `neg` and quantified variables. Test: "Kim can sing." and "Kim must sing." are refused naming the modal's predicate, not a variable.

4. **Two kinds of refusal.** One table in `lf.py`, the only home, classifies every refusal code as `final` or `reading`. `final` means the sentence was understood and the store cannot hold what it means, so the search ends. `reading` means this reading is unusable, so try the next. Every `final` code has a test with the sentence that motivated it. Record in `DECISIONS.md` that this replaces the words "among those that are not refusals" in `SPEC.md`.

5. **Reading choice, written down once.** Put the exact order of criteria as a numbered list in `DECISIONS.md`, and as a comment at the one place in the code that applies it: refusals, store overlap, the swallowed-word measure, parser order. For each criterion add two tests: a sentence where it decides, and a sentence where it must not change the outcome.

6. **Stratified negation.** Build the dependency graph of the rules. Assign each rule a stratum so that a rule with a negated body atom is in a higher stratum than every rule that can derive that atom. Run each stratum to fixpoint before starting the next. A rule set with a cycle through negation is refused when the rule is told, with `NEGATION_CYCLE`. Test: a rule set where the negated atom only becomes derivable in a later round. The fact that depends on its absence must not be stored.

7. **Repeats by meaning.** A tell is a repeat when its printed logical form, after names and pronouns are resolved, equals that of an earlier told sentence still in force. A repeat stores nothing and replies "already told", citing the earlier sentence. This replaces comparison by text. Consequence to keep: "Kim owns a dog." told twice creates one dog.

8. **Preposition senses.** A told fact must answer its own question. First check whether any reading of the question carries the predicate that was stored. If one does, the overlap score must select it, so fix the scoring. Only if no reading does: when matching a question atom whose predicate is a preposition, accept a stored predicate with the same lemma and the same part of speech but a different sense, and print the widening, for example `in_p_state matched as in_p_loc`. This applies to prepositions only. Test: the sentence pair from `REVIEW.md`.

Then verify, each with a test: a question whose wanted variable appears in no positive atom is refused; the repl never exits on an input sentence, and an internal error prints one line, continues, and reports in full to stderr.

Acceptance: all four unresolved findings in `REVIEW.md` are marked fixed with the commit that fixed them.

### Phase 10: describing a thing

"Who is X?" and "What is X?" with a known name return a new logical form, `Describe(entity)`. The answer lists every fact that mentions the entity, told facts first, then derived ones. An unknown name gives `Unknown`.

### Phase 11: conditionals

"If A, B." and "B if A." become a `Rule` with A as body and B as head. Names are constants, so the rule may be ground. A conditional containing a pronoun is refused until phase 13.

Sentences: "If Kim owns a dog, Kim is happy." "Tweety flies if Tweety is a bird." "If a robin sings, Kim is happy."

### Phase 12: negation over bare and indefinite nouns

A negated statement whose object is a bare noun or an indefinite is a rule that derives negative facts: "Kim does not like fish." means that for every fish, Kim does not like it. Printed: `rule not _like_v_1(_, kim, X) :- _fish_n_1(X)`.

The review already built this. Verify it against the dialogue, and do not rebuild it.

Add negated questions, which are currently refused: "Does Kim not like Nemo?" is the plain question with the answer inverted. `Yes` becomes `No`, `No` becomes `Yes`, and `Unknown` and `Conflict` stay as they are. Absence of a fact is still `Unknown`.

Dialogue: tell "Kim does not like fish." and "Nemo is a fish." Then "Does Kim like Nemo?" is `No`, with a proof. "Does Kim like Tweety?" is `Unknown`. "Does Kim not like Nemo?" is `Yes`. "Does Kim not like Tweety?" is `Unknown`.

### Phase 13: pronouns

- First and second person: two fixed entities, `user` and `tolk`. "I" and "me" are `user`. "You" is `tolk`. In answers `user` is worded as "you" and `tolk` as "I".
- Third person: the most recently mentioned entity, from earlier sentences or earlier in the same sentence, that agrees in number. Keep a `mention(sentence, position, entity)` table. If the two most recent candidates were mentioned in the same sentence and both agree, refuse with `AMBIGUOUS_PRONOUN`. There is no gender knowledge, so "he", "she" and "it" resolve alike.
- Every resolution is shown before storing: `it = tweety`.

Dialogue: "I am a person." then "Am I a person?" is `Yes`. "Are you a cat?" is `Unknown`. "Tweety is a robin. It sings." stores that Tweety sings. "Kim likes Sandy. She is happy." is refused as ambiguous.

### Phase 14: numbers

- A cardinal on an indefinite in a statement creates that many distinct anonymous things.
- "How many N ...?" returns a count of distinct things.
- A yes or no question with a cardinal means at least that many.
- Digits and number words are both accepted, from whatever the grammar provides.
- Arithmetic, "more than" with a number, "most" and fractions are refused.

Dialogue: "Kim owns two cats." then "How many cats does Kim own?" is 2. "Does Kim own two cats?" is `Yes`. "Does Kim own three cats?" is `Unknown`. Telling "Kim owns a cat." afterwards makes the count 3, because an indefinite always introduces a new thing.

### Phase 15: coordination

The review made every conjunction a refusal. This phase replaces that.

"And" between names, noun phrases and verb phrases distributes: "Kim and Sandy are happy." stores two facts. "Or" in a statement is refused. "Or" in a question is `Yes` if either side is. Collective readings are ignored, and that limit is noted in `DECISIONS.md`.

### Phase 16: unknown words

Record fixtures for sentences with invented words: "Tweety is a blorp." "Every blorp flibbers." "Tweety is glorpy." "Does Tweety flibber?"

Find out from the fixtures how the grammar marks a word it does not know. If it supplies a predicate with a recoverable lemma and part of speech, treat it like any other predicate of that class. If it gives no reading, refuse with `UNKNOWN_WORD` and the word. Write what you found in `PROGRESS.md`.

Acceptance: after the two statements, "Does Tweety flibber?" is `Yes`, or all four are refused with `UNKNOWN_WORD`. Either is a pass. A crash or a wrong fact is not.

### Phase 17: a public interface

Expose in `tolk/__init__.py` exactly:

- `read(text, known_predicates=frozenset()) -> logical form or Refusal`. It parses, compiles and chooses a reading, using `known_predicates` for the overlap score when no store is given.
- The logical form types and `printed(lf) -> str`.
- `Mind`.

Nothing else is public. Then run the checkpoint.

## Part B: engine

Part B changes what the engine means. Read all of Part B before starting phase 18.

### Phase 18: defaults and the conflict policy

**Two kinds of rule.** A bare plural generic ("Birds fly.", "Penguins do not fly.") is a default rule: it holds unless something overrides it. "Every", "all", "each", "no" and conditionals give strict rules. Printed forms differ: `rule` and `default`. This changes "Birds are animals." in tier A from strict to default. Its dialogue results do not change.

**Strength, strongest first.**

1. A told fact.
2. A fact derived by strict rules only.
3. A fact whose derivation uses at least one default rule.

When a fact and its opposite are both supported, the stronger side wins and the weaker is defeated. When both are at level 1 or 2, nothing wins: the result is `Conflict`, as in `SPEC.md`. That keeps the tier B dialogue unchanged.

**Between two defaults**, apply the policy list in order until one criterion separates them:

- `specific`: rule A beats rule B if A's body implies B's body. Test it by asserting A's body about a fresh thing in a scratch context and checking whether B's body follows.
- `trusted`: the rule whose source sentence has the higher trust wins. `Mind.tell(text, trust=n)` sets it. The default is 0.
- `recent`: the rule from the later sentence wins.

If the list runs out, neither wins and the result is `Conflict`.

**Telling.** A told fact that contradicts a level 3 conclusion is accepted, and the conclusion is defeated. A told fact that contradicts level 1 or 2 is still refused, as before.

**Computation.** Derived facts are a cache over told facts and rules.

1. Compute the strict closure.
2. Compute the default closure on top, skipping any rule instance in a `blocked` set.
3. For each pair of opposite facts, decide a loser by the rules above. Add the loser's rule instance to `blocked`.
4. If `blocked` grew, discard the default closure and go to step 2. `blocked` only grows, so this ends.

Record each defeat in `defeat(rule, bindings, by_fact, reason)`. Rebuild the cache when a tell adds a rule, a negative fact or a merge. A plain positive fact may be added incrementally only while no default rule exists. Incremental defeat is out of scope.

Proofs show defeats: a `No` that won over a default says which rule it defeated and by which criterion.

**Universal questions.** "Is every robin a bird?" is currently refused. Answer it with the same scratch-context test that `specific` uses, from the one shared function: assert the question's restriction about a fresh thing, derive, and check its conclusion. If it follows by strict rules, the answer is `Yes`. If it follows only through a default, the answer is `Yes, by default`. If its opposite follows, `No`. Otherwise `Unknown`. Known instances are never used as evidence: three birds that fly do not make "every bird flies" true.

Dialogue, in a fresh store: "Birds fly." "Every penguin is a bird." "Penguins do not fly." "Pingu is a penguin." "Tweety is a bird."

| Input | Result |
|---|---|
| Does Tweety fly? | Yes |
| Does Pingu fly? | No, by `specific`, defeating "Birds fly." |
| the same with `policy=()` | Conflict |
| Tweety does not fly. | stored, defeating the default |
| Does Tweety fly? | No |

The scale test from phase 2 must still pass.

### Phase 19: revision

- `Mind.retract(sentence_id)` removes what that sentence told and rebuilds the cache. Record it in `revision(sentence, reason)`. The sentence row stays.
- `Mind.diagnose()` returns, for each conflict, the candidate sentences whose removal would end it: the told sentences and rule sentences in the two proofs. Order them weakest first: default rules before strict rules before told facts, then lower trust, then more recent.
- `Mind.observe(text)` is a tell at the highest trust, marked as an observation. An observation is never a candidate for removal.
- With `auto_revise` on, a tell or observation that creates a conflict retracts the first candidate that is not an observation, and says so. With it off, nothing is retracted and the conflict is reported with its candidates.
- English form: "Forget that S." retracts the most recent told sentence whose logical form equals that of S.

Dialogue, continuing the tier B store where "Does Pingu fly?" is `Conflict`: `diagnose()` lists "Every bird flies.", "Every penguin is a bird.", "Pingu is a penguin." and "Pingu does not fly." "Forget that every bird flies." Then "Does Pingu fly?" is `No` and "Does Tweety fly?" is `Unknown`.

### Phase 20: time

- A question matches a fact only if their tenses agree. "Kim lived in Oslo." then "Does Kim live in Oslo?" is `Unknown`, and "Did Kim live in Oslo?" is `Yes`.
- Facts with no event, such as "Tweety is a robin", are tenseless and match any tense.
- A derived event takes the tense of the verb in the rule's conclusion.
- A year attached to an event is stored as a modifier atom, as phase 5 already does for places.
- "Before" and "after" between two clauses store an ordering between their events. Ordering is transitive, and an event in an earlier year is before an event in a later year. These two are built-in axioms. Proofs name them as such.

Only simple past and simple present are handled. Future, perfect and progressive stay refused, as the review left them. Durations, "since", "until", "now", and change over time are refused.

Dialogue: "Kim arrived before Sandy left." "Sandy left before Lee sang." Then "Did Kim arrive before Lee sang?" is `Yes`. "Did Lee sing before Kim arrived?" is `No`. "Kim lived in Oslo in 2019." "Kim lived in Bergen in 2021." Then "Where did Kim live in 2019?" is Oslo.

This changes the tier C dialogue in one way: "Sandy arrived." then "Does Sandy arrive?" is now `Unknown`. Add that line.

### Phase 21: beliefs and reports

A verb whose object is a clause ("believes that", "says that", "knows that", "thinks that") creates a claim: a new context that holds the clause's facts, and a world fact linking the holder, the verb and the claim.

- Claim contexts do not inherit into the world, and the engine does not derive inside them.
- "Does Kim believe that Tweety flies?" is `Yes` only if a claim held by Kim under that verb contains exactly that content.
- "Who believes that Tweety flies?" returns the holders.
- "What does Kim believe?" lists Kim's claims, worded.
- All clause verbs are treated alike. "Knows" does not make its content true in the world. Note that limit.
- One level only. A claim inside a claim is refused.

Dialogue: "Kim believes that Tweety swims." Then "Does Tweety swim?" is `Unknown`. "Does Kim believe that Tweety swims?" is `Yes`. "Does Sandy believe that Tweety swims?" is `Unknown`.

### Phase 22: comparatives

- "A is taller than B." is one fact with a system-built predicate: `comp:` followed by the adjective's predicate, with arguments A and B. This is a deliberate exception to mirroring the grammar's predications: storing the plain adjective would wrongly make "Is A tall?" true.
- Per adjective, the comparison is transitive and asymmetric. Both are built-in axioms. "Is B taller than A?" is `No`.
- "Who is the tallest?" answers only if exactly one known thing is above all others it can be compared with, and the answer says "among those I know". Otherwise `Unknown`.
- "As tall as", "less tall than", measures and antonyms are refused. "Shorter" is its own adjective with no link to "taller".

Dialogue: "Kim is taller than Sandy." "Sandy is taller than Lee." Then "Is Kim taller than Lee?" is `Yes`. "Is Lee taller than Kim?" is `No`. "Is Kim tall?" is `Unknown`. "Who is the tallest?" is Kim.

### Phase 23: morphology of unknown words

This applies only to a word the grammar marks as unknown in phase 16's sense. Strip one affix, undo simple spelling changes (doubled consonant, dropped e, y to i), and accept the split only if the base is a predicate of the right class already in the store. Otherwise the word stays whole.

Hard rule 3 forbids content words in rules. Affixes are not content words, and one table of them, with one home, is allowed.

| Affix | Class | Meaning in the store |
|---|---|---|
| un-, non- | adjective from adjective | the word holds exactly when the base does not: two strict rules deriving negative facts each way |
| -er | noun from verb | a thing is one exactly when it does the verb: two strict rules |
| -able | adjective from verb | recorded only. The store has no notion of possibility, so no rule is added |

Every split is recorded in `morph(word, base, affix)` and shown before storing: `unglorpy = un + glorpy`. `Describe` mentions it.

Dialogue, after phase 16's sentences: "Rex is unglorpy." Then "Is Rex glorpy?" is `No`. "Pingu is a flibberer." Then "Does Pingu flibber?" is `Yes`. "Tweety is flibberable." is stored, with the split shown and no rule.

### Phase 24: wording through the grammar

The parser can run in reverse and produce English from a meaning structure. Use it to word facts, with the templates in `say.py` as the fallback.

- Skeletons: write a script that takes recorded fixtures of the basic patterns (name with one-place verb, name with verb and object, name with "is a" noun, name with adjective, negated forms of each) and turns each into a skeleton by replacing its predicates and names with slots. Skeletons are generated by the script from fixtures and stored as data. This is the one permitted way to produce a meaning structure that was not recorded directly.
- To word a fact, fill the matching skeleton and call the generator.
- Accept a generated sentence only if parsing and compiling it gives back exactly the fact you started from. Among accepted sentences take the shortest, and the first alphabetically on a tie.
- If nothing is accepted, use the template, and mark the wording as a template in debug output.

Acceptance: for every derived fact in the tier A dialogue, either a generated sentence passes the round trip, or the fallback is used and counted. Paste the count of each into `PROGRESS.md`. At least the one-place verb and "is a" patterns must generate.

Then run the checkpoint.

## Part C: SQUID

SQUID is at `https://github.com/richarah/squid`. It compiles English questions to SQL over an existing database, using the same parser and grammar. The aim is for SQUID to use `tolk.read` as its front end, in a form that could later be merged into SQUID's main branch.

### Phase 25: find out what is there

Clone SQUID beside this directory. Change nothing yet. Install it, run its tests, and try ten questions against a small SQLite database of your own. Write `SQUID_REPORT.md` in the tolk repository: what the code does, module by module; which tests pass; which of the ten questions give correct SQL; what overlaps with tolk; and any claim in SQUID's README that the code does not support.

If SQUID cannot be installed or run, write why and stop Part C there. That is a complete result.

### Phase 26: the back end

Work on a new branch in the SQUID clone. Do not push.

- Add one module that turns a tolk `Ask` or `Describe` into SQL, given a mapping from predicates to tables and columns. Build the SQL with the SQL library SQUID already uses.
- The mapping is derived from the database schema by SQUID's existing schema linking. Reuse it. If it cannot be reused, say why in the report and write the smallest replacement.
- The set of predicates the schema can express is passed to `tolk.read` as `known_predicates`.
- Statements, rules, claims and anything from Part B are not SQUID's business. Given one, it returns a refusal.
- Leave SQUID's existing pipeline in place behind its existing entry point. Add the new path beside it under a clear name. Do not delete the old one.

Acceptance, as a differential test:

1. Build a small SQLite database: people, dogs, cats, an ownership table, a likes table. About twenty rows.
2. Tell tolk the same facts as English sentences generated from those rows.
3. Ask fifteen questions of both: who, which, how many, yes or no, with and without negation.
4. For each, the rows returned by SQUID's SQL must equal tolk's answer. Report every disagreement. A disagreement is a bug in one of the two, and you find which.

SQUID's own tests that passed in phase 25 must still pass.

## Out of scope

Possibility and obligation, durations and change over time, measures and units, claims nested inside claims, computing how far to trust a source, importing outside knowledge, a C++ port, a GPU path, and any change to libglot.

## Finish

Rerun every test and every dialogue in both repositories. End `PROGRESS.md` with: the phase table, the coverage numbers from `scripts/coverage.py` before and after, every refusal code and what triggers it, every built-in axiom, the count of generated against template wordings, and what you would do next.

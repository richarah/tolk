# SQUID report

Phase 25 of SPEC2. SQUID was cloned to `/home/richarah/squid` (commit 3807d98, "verified rules") and nothing in it was changed. Every number below is from a command run in this session. Scratch files (the test database, the scripts that tried the questions) are in `/home/richarah/squid_work`, outside both repositories.

## Setup

- `pip install -e '.[dev]'` fails: the build requires `mypy[mypyc]` and compiles the modules, and mypy reports errors in `squid/compiler.py` (for example `compiler.py:492`, `compiler.py:519`), so the build stops. The README says `pip install squid` and describes the mypyc build as an optimisation. Dependencies were installed by hand and the source used through `PYTHONPATH`.
- `scripts/setup_erg.sh` asks for `erg-2024-ubuntu-perplexity.dat` from the ACE download site; that URL returns 404. The ACE binary and the 2018 grammar image from the tolk repository were copied in instead (the same ACE 0.9.34).

## What the code does, module by module

| Module | Lines | What it does |
|---|---|---|
| `squid/__init__.py` | 145 | `compile(question, schema, ...)`: writes a TDL lexicon from the schema, runs ACE through `ERGParser`, picks a parse by schema fit, links predicates to the schema, compiles to SQL. `from_dmrs` skips the parser. |
| `squid/parser.py` | 372 | Runs the ACE binary with `subprocess`, one-shot or persistent, reads MRS text out of ACE's output, converts to DMRS with PyDelphin. |
| `squid/lexicon.py` | 221 | Generates TDL lexical entries for table and column names. |
| `squid/disambiguator.py` | 174 | Scores each parse by how many predicates match tables, columns or values, and keeps the best. |
| `squid/linker.py` | 412 | Matches predicates to schema elements: exact, inflection (inflect), lemma (lemminflect), fuzzy (rapidfuzz, 85). |
| `squid/schema.py` | 422 | `Schema` from SQLite, Spider JSON or SQLAlchemy; tables, columns, foreign keys. |
| `squid/compiler.py` | 526 | Walks a DMRS graph, builds a query plan and emits SQL through sqlglot. |
| `squid/rules.py` | 692 | The rules as data: 297 entries across quantifiers, comparisons, aggregations, connectives, modifiers, prepositions, arithmetic, set operations. |

## Tests

`PYTHONPATH=. .venv/bin/pytest -q tests`: 84 passed, 5 failed.

- `test_lexicon.py::test_tdl_avoids_duplicates` (finds 0 entries, expected 1).
- `test_rules.py::test_quantifier_rules`, `test_comparison_rules`, `test_aggregation_rules`, `test_connective_rules`: each indexes a rule as a dict (`["sql_op"]`) and `Rule` is a class, so `TypeError: 'Rule' object is not subscriptable`.

No test starts the parser or calls `squid.compile`: `grep` finds no use of `ERGParser` or `compile(` in `tests/`. The 84 passing tests check rule data, schema loading, linking and TDL text. Nothing tested connects ACE to SQL.

## Ten questions

The database (`pets.db`, five tables, 17 rows) is the one phase 26 will use: person, dog, cat, owns and likes tables.

1. **`squid.compile` itself: all ten fail** with `SquidParseError: ERG could not parse`. The cause is not the grammar. `compile` passes `--extra-lexicon <file>` to ACE, and ACE answers `unrecognized option '--extra-lexicon'` (its usage line lists `-1 -n -R -f -e -g -G` and no such option; `strings` on the binary shows none). The error is caught and replaced by the message above.
2. **`ERGParser` on its own** (no lexicon): all ten fail with `No valid DMRS parses`. ACE prints `SENT: <sentence>` before the MRS and a `;  (derivation ...)` after it; `_extract_mrs` tries to decode each blank-line-separated block as SimpleMRS, the decode raises `MRSSyntaxError` on the `SENT:` line, and a bare `except Exception: continue` drops it. Confirmed by decoding ACE's output by hand.
3. **Parsing with PyDelphin's ACE interface instead, then `disambiguate`, `link` and `DMRSCompiler` (the rest of SQUID, unchanged):**

| Question | SQL SQUID gave | Result | Correct? |
|---|---|---|---|
| How many dogs are there? | `SELECT COUNT(*) FROM dog` | 3 | yes |
| How many cats are there? | `SELECT COUNT(*) FROM cat` | 2 | yes |
| How many people are there? | `SELECT COUNT(*) FROM person` | 4 | yes |
| Which people exist? | `SELECT COUNT(*) FROM person` | 4 | no: asked for the people, got a count |
| What are the names of the dogs? | `SELECT person.name FROM person INNER JOIN person ON owns.person_id = person.id INNER JOIN dog ON owns.dog_id = dog.id` | SQL error: ambiguous column | no: wrong table, joins `person` to itself |
| Who owns a dog? | `SELECT COUNT(*) FROM dog INNER JOIN dog ON owns.dog_id = dog.id` | SQL error: no such column `owns.dog_id` | no |
| Which dogs does Kim own? | same as above | SQL error | no |
| List the names of cats. | `SELECT person.name FROM person INNER JOIN person ON owns.person_id = person.id INNER JOIN cat ...` | SQL error | no |
| How many dogs does Lee own? | `SELECT COUNT(*) FROM dog INNER JOIN dog ON owns.dog_id = dog.id` | SQL error | no |
| Does Kim own a cat? | `SELECT COUNT(*) FROM cat INNER JOIN cat ON owns.cat_id = cat.id` | SQL error | no |

Three of ten give correct SQL, all three are "how many X are there" over one table. Every question that needs the ownership table, a name, or a person produces SQL that does not run: the join is built from the wrong tables (a table joined to itself, `owns` named in `ON` but never joined). The names of Kim and Lee never reach the SQL.

## What overlaps with tolk

- Both use ACE and the ERG, and both read the parser's MRS through PyDelphin. tolk reads MRS directly; SQUID converts to DMRS.
- Both keep a persistent parser session (tolk does; SQUID's `compile` does not, see below).
- Both map predicates to a domain vocabulary. SQUID's schema linking (exact, inflection, lemma, fuzzy) is what phase 26 asks to reuse; tolk has no schema.
- Both refuse or fail on what they cannot map. tolk refuses with a reason and never partly stores; SQUID raises, or hides the error.
- Different: SQUID has no store, no reasoning, no proofs, and treats a question as a pattern over a schema. tolk's logical forms (`Ask`, `Describe`) are the thing phase 26 would turn into SQL.

## Claims in the README that the code does not support

- "`pip install squid`" and the mypyc speed-up: the build fails (above).
- Schema lexicon injection ("These are loaded into ACE alongside the ERG at parse time"): ACE has no `--extra-lexicon` option, so the mechanism cannot work with the ACE named in the README; a lexical entry has to be compiled into the grammar image.
- "Persistent ACE process" as an optimisation, and "~100-500ms (with persistent parser)": `squid.compile` builds a new `ERGParser` for every question and never starts it, so each question spawns ACE once. No latency was measured.
- "Every output traces to named rules" and "~40 structural rules": `rules.py` holds 297 entries; whether a given output traces to one was not checked. What the compiler produced for the six join questions is not traceable to the schema's foreign keys.
- "~40-60% estimated" accuracy: the Spider benchmark script was not run (no Spider data here); on the ten questions above the result is 3 of 10 for the stages after the parser, 0 of 10 for the entry point.
- "ERG 2024 grammar" in setup: the download URL is 404.
- Errors: `except Exception` appears eight times in `squid/`; the two that hide the parse failures are in `compile` and `_extract_mrs`.

## What this means for phase 26

SQUID's entry point does not run against any ACE and grammar this session could get, so SQUID's existing pipeline cannot be the behaviour to preserve: there is none to preserve beyond its unit tests (84 passing, which phase 26 must keep passing). The compiler stage and the linker work on DMRS from a different parser. The schema linking is reusable (`link` takes a DMRS and a schema, and does not need the parser). The SQL back end phase 26 asks for takes tolk's logical forms, not DMRS, so it does not depend on the compiler's join logic, which the table above shows to be wrong for every multi-table question.

## Phase 26: the back end

Branch `tolk-backend` in `/home/richarah/squid`, commit ab9f34e, not pushed. Three files added, nothing else changed; the old pipeline and its entry point are as they were.

- `squid/tolk_backend.py`: `to_sql(logical_form, schema)` turns a tolk `Ask` or `Describe` into SQL with sqlglot; `predicates(schema)` gives the set to pass to `tolk.read` as `known_predicates`. A statement, rule, claim, comparison, universal question or any predicate the schema lacks gives a tolk `Refusal`. The mapping from predicate to table is SQUID's `linker.match_table` (reused, not rewritten); the relation shape (a table with two or more foreign keys, its first foreign key the subject) and the choice of column for each role are new, since SQUID's linker works on DMRS and links only words to tables and columns. A role that more than one column could fill (a name that might be a dog or a cat) gives the union over each column.
- `scripts/differential_tolk.py` and `tests/test_tolk_backend.py`: the differential test. The nineteen rows were told to tolk as nineteen sentences ("Kim is a person.", "Kim owns Rex." and so on, generated from the rows), and fifteen questions asked of both.
- SQUID's own tests: 84 passed, 5 failed before and after (the same five, listed above). With tolk on the path the new file adds 19 passing tests (103 passed). Without tolk the new file is skipped at collection (`importorskip`), because tolk is not a dependency of SQUID.

Result: **12 of 15 agree. 3 disagree, and all three are one cause.**

| Question | tolk | rows |
|---|---|---|
| Does Kim own Fido? | Unknown | none |
| Does Kim not own Fido? | Unknown | one |
| Which dogs does Kim not own? | Unknown | Fido, Spot |

tolk never answers No from the absence of a fact (SPEC.md: "Absence of a fact is Unknown, never No"); a database reads the absence of a row as false. Neither is a bug: the two systems hold different assumptions, and a question with no stored answer or a negation over a missing row has no answer both can give. The twelve that agree are the three counts and the who and which questions, and the three yes-or-no questions and the one negated question whose rows exist. "Does Kim not own Rex?" agrees: tolk says No (the fact is told), the query returns no rows.

Found on the way: tolk reads "How many dogs are there?" as a refusal (`GRAMMAR_ARTIFACT: place_n`), so it is not among the fifteen; SQUID's own pipeline cannot take the same sentence in either case (above).

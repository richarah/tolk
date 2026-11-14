# DECISIONS

- Installer: `uv` creates `.venv` and installs the package. `pip` and `ensurepip` are missing on this machine. `uv` is not a runtime dependency.
- Parser session: one `delphin.ace.ACEParser` opened on first use and kept open in `tolk/erg.py`. The idea of keeping the session open comes from the description of SQUID in SPEC.md. SQUID's code was not read.
- Reading choice: only readings whose sentence index is bound by a non-`unknown` predicate are eligible (see PLAN.md item 9). Fixtures: "Every bird flies" and "Superman flies" have noun-reading parses that bind the index only through `unknown`.
- Fixture slugs: lowercase text with runs of non-alphanumerics replaced by `_`.
- Compound names: the head is `ARG1` and is last in the text, so the constant is `ARG2` + `_` + `ARG1`.
- Single home: slug and sentence list live in `tests/helpers.py`, imported by `scripts/record.py` and the tests. The user's update says each fact has one home.
- Mapping shape: `map_ep(ctx, ep)` per family module, called in fixed order from `compile.py`. No registry, because a dict of handlers would be the registry the spec forbids.
- Reading choice: only eventive readings compete (an EP takes the sentence index as ARG0 and is not `unknown`). Among non-refused candidates the one with the most predicates in the store wins, ties by parser order. If every eventive reading refuses, the first eventive reading's refusal is returned, not reading 0's, because reading 0 is often a noun parse.
- Restriction of a wh word: an abstract predicate (no leading underscore) under `which_q` gives no atom and is not named in code. The wanted variable is simply unrestricted.
- Copula: `_v_id` (the identity sense) is recognised by its suffix. An indefinite or universal complement is aliased to the subject, so it adds atoms to the subject and creates nothing. A named complement is refused `IDENTITY_NOT_YET` until phase 4.
- Unexpressed arguments: an i-variable mentioned by no other predication is dropped; a gap before an expressed argument is refused `ARGUMENT_GAP`.
- Rule shape: a universal at top level makes a rule. Its restriction (and the restrictions of quantifiers nested in it) is the body; everything else is the head. Head variables the body does not bind are created (printed with `!`).
- Lemma scan exemption: `every`, `no`, `do`, `does`, `is`, `a`, `an`, `the`, `be` come from determiner and auxiliary predicates. The scan ignores them. Quantifier names are allowed in rules by SPEC rule 3. The copula is recognised by its sense suffix, not its lemma.
- Ask mode: every indefinite and every wh variable is a variable. Events are variables. Tell mode: events and indefinites become fresh constants \`e1..\`, \`a1..\`.
- `Reading` gained `top` (the LTOP handle). It is needed to find the main clause.

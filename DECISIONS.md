# DECISIONS

- Installer: `uv` creates `.venv` and installs the package. `pip` and `ensurepip` are missing on this machine. `uv` is not a runtime dependency.
- Parser session: one `delphin.ace.ACEParser` opened on first use and kept open in `tolk/erg.py`. The idea of keeping the session open comes from the description of SQUID in SPEC.md. SQUID's code was not read.
- Reading choice: only readings whose sentence index is bound by a non-`unknown` predicate are eligible (see PLAN.md item 9). Fixtures: "Every bird flies" and "Superman flies" have noun-reading parses that bind the index only through `unknown`.
- Fixture slugs: lowercase text with runs of non-alphanumerics replaced by `_`.
- Compound names: the head is `ARG1` and is last in the text, so the constant is `ARG2` + `_` + `ARG1`.
- Single home: slug and sentence list live in `tests/helpers.py`, imported by `scripts/record.py` and the tests. The user's update says each fact has one home.
- Mapping shape: `map_ep(ctx, ep)` per family module, called in fixed order from `compile.py`. No registry, because a dict of handlers would be the registry the spec forbids.

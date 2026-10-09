# Continuation backends used by the pipeline

This directory contains implementation dependencies of the canonical
eight-stage workflow in `../run_pipeline.py`:

- `lidlab/backends.py` and `lidlab/data.py` support the ConLID adapter.
- `native/` and `scripts/build_native.py` build the fastText continuation
  executable used for NLLB, GlotLID, OpenLID, and related evaluations.
- `tests/` contains implementation-level backend checks.

The historical standalone result snapshots and exploratory notebooks are not
part of this branch. Researchers should run `../run_pipeline.py` rather than
copy scores from this backend package. Keep `THIRD_PARTY_NOTICES.md` and
`native/fasttext/LICENSE` with the bundled native source.

# Extendible hashing lab review — 2026-04-20 — initial slice

## Pass 1 — docs / runnable-command review
- Re-read the new project README after the first green test run and checked the documented test command against the actual repo environment.
- Issue found: the README pointed to `pytest`, but this repo run did not have `pytest` installed, so the copy-paste verification path in the docs was wrong.
- Fix: updated `projects/extendible-hashing-lab/README.md` to use the stdlib `unittest` command that actually passes in this repository.

## Pass 2 — snapshot identity / future-split review
- Re-read the snapshot loader with the goal of finding corruption cases that would only show up after persisting and reloading a table.
- Issue found: malformed snapshots could silently reuse duplicate `bucket_id` values or set `next_bucket_id` too low, which would allow future splits to overwrite existing bucket identities.
- Fix: tightened `ExtendibleHashTable.from_snapshot` validation to reject duplicate bucket ids and require `next_bucket_id` to advance beyond every existing bucket id, and added regression tests for both cases.

## Pass 3 — snapshot routing / lookup-correctness review
- Replayed the load path mentally from persisted JSON into a live table and compared bucket contents against the directory routing rule.
- Issue found: a malformed snapshot could place a key into a bucket that its hash bits would never route to, causing silent lookup failures after load even though the JSON shape looked valid.
- Fix: added bucket-entry routing validation inside `from_snapshot` and a regression test that proves misrouted keys are rejected.

## Final verification
- `python3 -m py_compile projects/extendible-hashing-lab/extendible_hashing_lab.py tests/test_extendible_hashing_lab.py`
- `python3 -m unittest tests.test_extendible_hashing_lab -v` (`10/10`)
- smoke-tested `run`, `inspect --format markdown`, `lookup`, and `delete` with `projects/extendible-hashing-lab/sample_workload.json`
- regenerated the committed sample artifact bundle under `docs/artifacts/extendible-hashing-lab/`
- `git diff --check`

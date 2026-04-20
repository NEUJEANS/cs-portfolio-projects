# extendible-hashing-lab delete/merge slice — 2026-04-20T22:56:07Z

## Sync status
- Checked `main`, `origin`, `git fetch origin`, and `HEAD...origin/main` before editing.
- Remote drift: none (`ahead/behind 0/0` before the slice commit), so finishing the existing local delete/merge slice was safe.

## What changed
- shipped delete-time bucket merge support plus directory shrink after merges in `projects/extendible-hashing-lab/extendible_hashing_lab.py`
- added a delete-heavy workload fixture that grows to global depth 2 and shrinks back to depth 0
- committed delete-heavy snapshot/report/inspect artifacts under `docs/artifacts/extendible-hashing-lab/`
- refreshed the project README and both project/root checklists to expose the full split → merge → shrink lifecycle
- added/updated tests for merge, cascade shrink, no-merge-on-depth-mismatch, merged snapshot round-trips, workload history, and snapshot alias-count invariants
- recorded the slice checklist, self-test note, and review log for resumable follow-up work

## Tests and reviews run
- `python3 -m py_compile projects/extendible-hashing-lab/extendible_hashing_lab.py tests/test_extendible_hashing_lab.py`
- `python3 -m unittest tests.test_extendible_hashing_lab -v` (`16/16`)
- smoke runs:
  - `python3 projects/extendible-hashing-lab/extendible_hashing_lab.py run --input projects/extendible-hashing-lab/delete_heavy_workload.json --output docs/artifacts/extendible-hashing-lab/delete_heavy_workload_snapshot.json --report docs/artifacts/extendible-hashing-lab/delete_heavy_workload_report.md --title 'Extendible hashing delete-heavy merge/shrink report'`
  - `python3 projects/extendible-hashing-lab/extendible_hashing_lab.py inspect --snapshot docs/artifacts/extendible-hashing-lab/delete_heavy_workload_snapshot.json --format markdown > docs/artifacts/extendible-hashing-lab/delete_heavy_snapshot_inspect.md`
  - `python3 projects/extendible-hashing-lab/extendible_hashing_lab.py lookup --snapshot docs/artifacts/extendible-hashing-lab/sample_workload_snapshot.json user:1009`
  - `python3 projects/extendible-hashing-lab/extendible_hashing_lab.py delete --snapshot docs/artifacts/extendible-hashing-lab/sample_workload_snapshot.json --output <tmp> user:1041`
- review passes completed and fixes recorded in `docs/reviews/extendible-hashing-lab-2026-04-20-delete-merge.md`
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (clean)

## Feature commit
- `fb338f2` — `Add extendible hashing delete merge lifecycle`

## Next step
- add benchmark comparisons against cuckoo hashing or B-tree lookup/update workloads so this lab can tell a stronger performance trade-off story.

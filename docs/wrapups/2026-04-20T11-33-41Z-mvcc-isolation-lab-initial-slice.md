# MVCC isolation lab wrap-up — 2026-04-20T11:33:41Z

- Project: `mvcc-isolation-lab`
- Feature commit: `2d9e58c` (`Add mvcc isolation lab initial slice`)

## What changed
- added a new database-concurrency portfolio project that simulates `read-committed`, `snapshot`, and optimistic `serializable` isolation on deterministic JSON schedules
- implemented scenario validation, step-by-step traces, invariant checks, and `validate` / `run` / `compare` CLI commands in `projects/mvcc-isolation-lab/mvcc_isolation_lab.py`
- committed two sample scenarios that tell clear portfolio stories: doctor-on-call write skew and a repeatable-read window with a concurrent writer
- generated recruiter-friendly Markdown comparison artifacts under `docs/artifacts/mvcc-isolation-lab/` and added project/root checklist, research, learning, and review notes so the slice is resumable
- added regression coverage for validation errors, write-skew behavior, repeatable-read behavior, JSON output, and Markdown export wiring

## Tests and reviews run
- `python3 -m py_compile projects/mvcc-isolation-lab/mvcc_isolation_lab.py tests/test_mvcc_isolation_lab.py`
- `python3 -m unittest tests.test_mvcc_isolation_lab -v` (`10/10`)
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py validate projects/mvcc-isolation-lab/doctor_on_call.json`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/doctor_on_call.json --markdown-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_compare.md`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/repeatable_read_window.json --markdown-out docs/artifacts/mvcc-isolation-lab/repeatable_read_window_compare.md`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py run projects/mvcc-isolation-lab/repeatable_read_window.json --isolation read-committed --json`
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- review log: `docs/reviews/2026-04-20-mvcc-isolation-lab-initial-slice.md`

## Next step
- add timeline/SVG schedule exports so readers can see begin/read/write/commit windows and version changes without parsing the raw JSON trace

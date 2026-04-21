# Library manager SQLite review — 2026-04-21 — dashboard export slice

## Pass 1 — reproducibility review
- Reviewed the new snapshot export as if the sample dashboard would be committed and regenerated later.
- Issue found: `generated_at` always used the current clock time, so repeated exports of the same seeded dataset would drift even when nothing meaningful changed.
- Fix: added an optional `generated_at` snapshot field plus CLI `--generated-at` support, then covered it in tests.

## Pass 2 — historical snapshot correctness review
- Reviewed the dashboard semantics with a past `--date` instead of only “today”.
- Issue found: future returns and future checkouts still polluted earlier snapshots, which made `stats`, `current_circulation`, `recent_activity`, and `loan_history` misleading for historical exports.
- Fix: changed the circulation/history queries to treat the reference date as an as-of boundary, and added tests that verify future returns stay active/overdue in earlier snapshots.

## Pass 3 — export hygiene review
- Reviewed the new renderers and tests for warning-free, stable output.
- Issue found: Markdown cell escaping used an invalid `\|` string escape, which raised a Python `SyntaxWarning` and made the renderer look sloppier than the rest of the project.
- Fix: corrected the Markdown escaping, tightened assertions around rendered timestamps, and refreshed the README/checklist docs so the slice is easy to resume.

## Final verification
- `python3 -m py_compile projects/library-manager-sqlite/library_manager.py projects/library-manager-sqlite/test_library_manager.py`
- `cd projects/library-manager-sqlite && python3 -m unittest -v test_library_manager.py` (`15/15`)
- seeded smoke export via `/tmp/library_dashboard_seed_smoke.py`, regenerating committed Markdown and HTML dashboard artifacts with a fixed snapshot timestamp
- `git diff --check`
- TruffleHog secret scan passed: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

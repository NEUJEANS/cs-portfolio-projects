# library-manager-sqlite borrower trend breakdowns

- Timestamp: 2026-04-21T14:16:51Z
- Feature commit: `d7cc03e`

## What changed
- added a new `borrower-trends` CLI export that ranks the top borrower cohorts touching the selected date range and emits borrower/day CSV rows plus an SVG cohort dashboard
- extended the library analytics layer with borrower-level trend snapshots, deterministic cohort selection, and cohort summary metrics such as peak active loans, peak overdue loans, and active-day counts
- committed deterministic sample borrower trend artifacts under `docs/artifacts/library-manager-sqlite/`
- refreshed the project README plus checklist, research, learning, and review notes so the slice is resumable

## Tests and reviews run
- `python3 -m py_compile projects/library-manager-sqlite/library_manager.py projects/library-manager-sqlite/test_library_manager.py`
- `cd projects/library-manager-sqlite && python3 -m unittest -v test_library_manager.py`
- real CLI smoke via committed artifact generation for `borrower-trends`
- deterministic rerun checks for borrower CSV and SVG exports with `cmp`
- `git diff --check`
- 3 review passes logged in `docs/reviews/2026-04-21-library-manager-sqlite-borrower-trend-breakdowns.md`

## Next step
- add category or genre metadata so the analytics pack can grow from borrower cohorts into stacked subject-level circulation stories

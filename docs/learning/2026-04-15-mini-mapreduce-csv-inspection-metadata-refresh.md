# Mini MapReduce CSV inspection metadata refresh — 2026-04-15

## Quick refresh
- `csv.DictWriter` emits empty fields for `None`, which is useful for keeping built-in-job rows schema-compatible with plugin rows.
- Comma-containing metadata like dataset-family lists should stay as a single CSV cell; `DictWriter` will quote them automatically.
- Stable column order matters for resumable portfolio artifacts and regression tests, so add new metadata columns explicitly near the existing plugin/job context.

## Self-test
- Planned header keeps plugin metadata before numeric benchmark metrics so spreadsheet viewers can freeze context columns.
- Expected plugin-family cell shape: `"default,exam-cram,project-week"`.
- Expected built-in row shape: blank plugin metadata columns, no schema branching.

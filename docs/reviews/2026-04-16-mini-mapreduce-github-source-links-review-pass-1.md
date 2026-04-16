# Mini MapReduce GitHub source links review — pass 1

Date: 2026-04-16 05:34 UTC
Project: `mini-mapreduce-lab`

## Focus
- inspection JSON/CSV schema compatibility
- project-level vs repo-level test coverage alignment

## Issue found
- Repo-level CSV header assertions still expected the pre-link schema and failed after adding `*_source_anchor` and `*_source_url` fields.

## Fix applied
- Updated `tests/test_mini_mapreduce.py` header expectations and row assertions to cover the new source-anchor/source-URL columns.

## Verification
- Re-ran targeted project and repo tests after the fix.

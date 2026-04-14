# Review pass 2 — markdown-notes-search persistent index

Date: 2026-04-14

## Focus
Review cache path handling and operational robustness.

## Issue found
- saving a custom nested cache path like `cache/index.json` would fail if the parent directory did not already exist.

## Fix
- create parent directories in `save_index_cache()` before writing the JSON payload.
- added automated coverage for nested cache paths.

## Result
- CLI users can choose organized cache locations without manual setup.

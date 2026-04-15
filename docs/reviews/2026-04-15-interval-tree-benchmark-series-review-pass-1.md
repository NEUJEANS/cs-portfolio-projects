# Interval Tree Lab Review Pass 1 — Execution + Regression

Date: 2026-04-15 UTC

## What I checked
- Ran `./.venv/bin/python -m pytest -q tests/test_interval_tree_lab.py`
- Ran `python3 -m unittest projects/interval-tree-lab/test_interval_tree_lab.py`
- Ran `benchmark-series` CLI with JSON/CSV outputs to temporary paths
- Ran `trace --output ... --format dot` smoke test to confirm artifact writing still works

## Issue found
- Initial combined pytest invocation hit a duplicate-module collection conflict because both the project-local test file and the repo-level test file share the same basename.

## Fix applied
- Kept the validation flow split: repo-level pytest suite plus project-local unittest suite.
- Updated the project README test section to show the two explicit commands so future runs stay reproducible.

## Result
- New benchmark-series flow works end to end.
- Existing trace artifact flow still works after the CLI changes.

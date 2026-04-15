# 2026-04-15 interval-tree-lab review pass 3

## Focus
Edge cases and regression coverage.

## Issue found
- the test suite covered valid interval parsing but did not explicitly lock in the failure case for reversed intervals.

## Fix applied
- added a regression test asserting that `parse_interval_spec("9-4:broken")` raises `ValueError`
- reran the unit tests and CLI demo after the change

## Result
- invalid-range handling is now explicitly protected by tests

# Expense Tracker Review Pass 1 — 2026-04-14

## Focus
Query/report correctness.

## Issue found
Monthly summaries ignored `--start-date` and `--end-date`, which made the CLI flags misleading for `summary --group-by month`.

## Fix
- added date-window filtering to `total_by_month(...)`
- wired CLI month summaries to pass the selected date range
- updated tests to assert filtered month output

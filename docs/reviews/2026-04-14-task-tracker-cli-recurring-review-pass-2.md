# 2026-04-14 task-tracker-cli recurring review — pass 2

## Focus
Edge cases in date advancement and test coverage.

## Issue found
- Monthly recurrence is the riskiest path because naive month increments break for dates like January 31.

## Fix applied
- Kept month advancement on a stdlib-only path using `calendar.monthrange(...)` and added a regression test that verifies `2026-01-31 -> 2026-02-28`.

## Result
- The recurring workflow now handles short-month rollover deterministically.

# Learning/self-test — library-manager-sqlite loan-history slice — 2026-04-21

## Refresh target
Small SQLite patterns for normalized circulation state.

## Quick refresh
- partial unique indexes can enforce one active row per entity subset
- aggregate queries with `SUM(CASE WHEN ...)` are enough for lightweight analytics
- `julianday(...)` differences are handy for return-time and lateness calculations
- migration/backfill can be incremental: preserve current behavior first, then normalize new writes

## Self-test
Before coding, sanity-checked the design with a short mental exercise:
- if a book is checked out twice over time, multiple `loans` rows should exist
- if a book is currently checked out, exactly one `loans` row should have `returned_at IS NULL`
- if an older DB only has the legacy `books.borrower` fields populated, the migration should recreate that single active loan row
- analytics should be derivable from SQL joins instead of Python-side bookkeeping

## Outcome
Safe to implement the slice as a normalized borrower/history upgrade without changing the lightweight CLI feel of the project.

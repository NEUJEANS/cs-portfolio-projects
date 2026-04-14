# 2026-04-14 Expense Tracker Refresh

## Quick refresh
- SQLite stores ISO dates well enough for range filtering because `YYYY-MM-DD` sorts lexicographically.
- `date.fromisoformat(...)` is a simple built-in validator for CLI date input.
- Lightweight SQLite migrations can be handled with `PRAGMA table_info(...)` plus `ALTER TABLE ... ADD COLUMN`.

## Self-test
- confirmed `date.fromisoformat('2026-04-14').isoformat()` round-trips cleanly
- used that pattern for CLI/date validation in the project slice

# Python/SQLite Refresh — Library Manager

Date: 2026-04-14

## Refreshed topics
- `sqlite3.Row` for named-column access
- lightweight schema migration using `PRAGMA table_info`
- ISO date handling with `datetime.date`
- case-insensitive search using `LIKE` over normalized patterns

## Self-test
1. How should due dates be stored for simple CLI portability?
   - As ISO `YYYY-MM-DD` text so SQLite queries and Python formatting stay simple.
2. How can an existing SQLite table be upgraded without dropping data?
   - Inspect columns with `PRAGMA table_info` and `ALTER TABLE ... ADD COLUMN` for missing fields.
3. What is the cleanest overdue rule here?
   - A book is overdue when it is checked out, has a due date, and `due_date < reference_date`.

## Implementation note
Keep the schema small and queryable; avoid premature borrower/history tables in this slice.

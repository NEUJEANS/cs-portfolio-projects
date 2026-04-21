# Research — library-manager-sqlite loan-history + analytics slice — 2026-04-21

## Goal
Upgrade `library-manager-sqlite` from a current-state circulation demo into a more interview-ready data-systems project with auditable loan history and borrower-level analytics.

## Sources checked
- SQLite `CREATE INDEX` docs: `https://sqlite.org/lang_createindex.html`
- SQLite `UPSERT` docs: `https://sqlite.org/lang_upsert.html`

## Notes
- SQLite supports partial indexes, which makes `CREATE UNIQUE INDEX ... WHERE returned_at IS NULL` a clean way to enforce "at most one active loan per book" while still allowing historical returned rows.
- A normalized borrower table plus a loan-history table tells a stronger state-transition story than storing only `borrower`, `checked_out_at`, and `due_date` on the current `books` row.
- Migration should preserve existing behavior for older databases. The safest minimal backfill is to reconstruct only still-active legacy checkouts into the new `loans` table; already-returned historical rows cannot be recovered from the old schema.
- Borrower creation can use `UPSERT`, but a plain `INSERT` with an `IntegrityError` fallback is slightly more version-tolerant and perfectly adequate for this local CLI.
- Basic circulation analytics can stay SQL-first: counts, overdue/returned splits, average configured loan length, average return time, and top borrowers all fit small aggregate queries.

## Decision
Implement:
- normalized `borrowers` and `loans` tables
- a partial unique index for one active loan per book
- migration/backfill for active legacy checkouts
- `history` and `stats` CLI commands so the audit trail is visible without opening SQLite manually

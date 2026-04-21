# library-manager-sqlite checklist

- [x] define the project scope and interview story for a SQLite-backed library circulation CLI
- [x] implement book creation, catalog listing, checkout, return, and overdue reporting flows
- [x] cover core lifecycle behavior with automated tests
- [x] refresh the project README with usage and future-improvement notes
- [x] upgrade catalog search to ranked SQLite FTS5 search with safe fallback to substring matching
- [x] support migration/backfill so older catalog databases gain the search index without manual rebuild steps
- [x] add fresh research and self-test notes for the search upgrade
- [x] log review passes and follow-up notes so the FTS slice is resumable later
- [x] add a borrower/loan-history table so circulation analytics are auditable instead of stored only on the current book row
- [x] expose history and circulation analytics commands so the new audit trail is visible in CLI demos
- [x] backfill still-active legacy checkouts into the normalized loan tables during migration
- [ ] add a small HTML or Markdown circulation dashboard export for recruiter-friendly portfolio screenshots

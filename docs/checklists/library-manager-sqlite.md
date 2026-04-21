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
- [x] add a small HTML and Markdown circulation dashboard export for recruiter-friendly portfolio screenshots
- [x] add chart-friendly trend exports (CSV or SVG) so the dashboard can evolve from a point-in-time snapshot into a small analytics pack
- [x] add borrower-level trend breakdown exports so the analytics pack can tell a stronger multi-borrower circulation story
- [x] add genre metadata plus genre-level trend exports so the analytics pack can tell a subject-level circulation story
- [x] add a genre/day heatmap export so the subject-level story is visible in one glance instead of separate cohort lines only

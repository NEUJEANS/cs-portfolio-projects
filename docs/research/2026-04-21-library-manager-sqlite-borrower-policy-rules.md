# Research — library-manager-sqlite borrower policy rules — 2026-04-21

## Goal
Add a policy-focused circulation slice so `library-manager-sqlite` demonstrates real operational constraints, not just catalog CRUD and after-the-fact analytics.

## External references checked
1. SQLite `CREATE TABLE` docs, fetched 2026-04-21 15:30 UTC
   - SQLite supports `CHECK`, `DEFAULT`, `PRIMARY KEY`, and `IF NOT EXISTS`, which is enough for a tiny persisted policy table with migration-safe defaults.
2. SQLite `UPDATE` docs, fetched 2026-04-21 15:30 UTC
   - A focused `UPDATE ... SET ... WHERE id = 1` is enough for a single-row policy store, and columns not named in the update remain unchanged.
3. SQLite `CREATE TRIGGER` docs, fetched 2026-04-21 15:30 UTC
   - Triggers are possible, but they are row-oriented and add more schema-level indirection than this lightweight CLI needs.

## Design takeaways
- Keep policy state in SQLite, not only in CLI flags.
  - That makes the project feel like a real circulation system with persistent rules.
  - Recruiter demos can show both live enforcement and saved configuration.
- Use one single-row `circulation_policy` table instead of a more generic key/value store.
  - The schema stays obvious and type-safe.
  - The project only needs a couple of policy knobs right now.
- Enforce borrower policy in Python during checkout rather than with SQLite triggers.
  - The error messages can stay human-readable.
  - The logic can reuse the same borrower status view used by the policy report.
- Export a policy snapshot as Markdown and HTML.
  - That turns the rules into another portfolio artifact instead of a hidden implementation detail.

## Slice chosen
Add:
- a persisted `circulation_policy` table with max active-loan limit and overdue-checkout blocking
- checkout-time enforcement with clear `LibraryError` messages
- a `policy` CLI that can inspect or update the rules
- Markdown and HTML borrower-compliance exports under `docs/artifacts/library-manager-sqlite/`

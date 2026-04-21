# library-manager-sqlite genre trend self-test

Date: 2026-04-21

## Quick refresh
- A single additive `genre` column is the simplest migration-safe way to enrich the existing SQLite catalog for subject analytics.
- Older databases need an explicit backfill to a stable default like `General`, otherwise analytics and list output can drift on null rows.
- The genre trend export should stay window-aware, deterministic, and separate from aggregate trend rows so downstream CSV consumers keep a stable schema.

## Self-test
1. Why add `genre` to `books` instead of introducing a many-to-many tag schema in this slice?
   - Because the goal is one meaningful vertical slice, not a taxonomy subsystem. A single column is enough to unlock subject-level analytics while keeping migration and README complexity low.
2. Why rank genres by loans touching the selected range instead of lifetime totals only?
   - Because the export should explain the chosen time window. A historically popular genre with no overlap in the selected range is less relevant than one driving the current chart.
3. Why keep a dedicated `genre-trends` CSV instead of folding genre columns into the aggregate `trends` export?
   - Because the aggregate export is one row per day, while genre breakdowns are one row per day per genre. Mixing them would make both artifacts harder to read and less stable for reuse.

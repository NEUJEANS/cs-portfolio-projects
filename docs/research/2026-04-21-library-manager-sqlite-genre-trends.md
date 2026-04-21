# Research — library-manager-sqlite genre trend breakdowns — 2026-04-21

## Goal
Add the smallest meaningful metadata upgrade that turns the library analytics pack from borrower-only stories into subject-level circulation stories.

## External references checked
1. SQLite docs, `ALTER TABLE`, fetched 2026-04-21 14:31 UTC
   - SQLite supports additive schema evolution with `ALTER TABLE ... ADD COLUMN`, which fits a migration-safe `genre` field on the existing `books` table.
   - A lightweight additive column is a better fit here than a larger tag/join-table redesign for a single vertical slice.
2. MDN, SVG `<title>`, fetched 2026-04-21 14:31 UTC
   - Use `<title>` for a short accessible name on the overall SVG and grouped chart regions.
   - Keep `<title>` as the first child for SVG 1.1 compatibility.
3. MDN, SVG `<desc>`, fetched 2026-04-21 14:31 UTC
   - Use `<desc>` for longer non-visual chart explanations.
   - Pair it with `aria-describedby` when the export contains multiple grouped panels.

## Design takeaways
- Add `genre` directly to `books` first.
  - This keeps the slice migration-safe and easy to explain.
  - Existing databases can default older rows to `General` without manual repair.
- Keep the original aggregate `trends` and borrower-oriented `borrower-trends` exports unchanged.
  - Genre analytics should be additive, not a replacement.
- Export genre breakdowns as both CSV and SVG.
  - CSV is better for spreadsheet follow-up and downstream charts.
  - SVG is better for recruiter screenshots and committed artifacts.
- Rank genres by loans touching the selected date range.
  - This keeps the chosen cohorts relevant to the requested window.
  - Tie-breaking by recent activity keeps the output deterministic and easier to defend in review.

## Slice chosen
Add a `genre` metadata field plus a new `genre-trends` CLI export that emits:
- genre/day CSV rows for the busiest genres touching the selected range
- an accessible SVG with a genre legend, active-loan panel, overdue-loan panel, and summary table
- deterministic sample artifacts committed under `docs/artifacts/library-manager-sqlite/`

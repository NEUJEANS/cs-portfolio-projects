# library-manager-sqlite borrower trend self-test

Date: 2026-04-21

## Quick refresh
- Prefer deterministic ranking for top cohorts so repeated exports pick the same borrowers when the underlying data is unchanged.
- Use the standard-library `csv` writer for borrower names because commas or quotes would make hand-built CSV rows fragile.
- Keep historical semantics aligned with the existing dashboard and trend exports: a loan is active on a day only if it was checked out by then and not yet returned before the day ends under the project’s current snapshot rules.

## Self-test
1. Why not fold borrower breakdown columns into the existing aggregate CSV?
   - Because the aggregate CSV is one row per day, while borrower breakdowns are one row per day per borrower cohort. Mixing them would make the original artifact harder to read and less stable for downstream use.
2. Why rank borrowers by loans touching the selected range instead of lifetime totals only?
   - Because the export should explain the chosen window. A borrower with old historic volume but no activity overlapping the selected range is less relevant to the current chart.
3. Why keep a summary table under the SVG charts?
   - Because trends alone show shape, but the table quickly answers total loans, peak active load, peak overdue load, and how often each cohort appears across the chosen window.

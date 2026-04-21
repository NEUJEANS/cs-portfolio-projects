# library-manager-sqlite genre heatmap review log

Date: 2026-04-21

## Review pass 1, summary-table layout
- Inspected the first generated SVG heatmap export after the implementation pass.
- Found issue: the summary header row and the first summary data row overlapped vertically, which made the bottom section harder to read in static screenshots.
- Fix: moved the first summary data row below the header block so the table reads cleanly.

## Review pass 2, metric wording accuracy
- Re-read the row-level labels and summary columns against the computed snapshot values.
- Found issue: the UI called the cumulative active-load metric `active-days`, but the value was actually loan-days because multiple simultaneous loans can contribute on the same date.
- Fix: renamed the visible label to `loan-days` in the heatmap SVG text and summary header.

## Review pass 3, validation and determinism
- Re-ran the full unittest suite plus a real CLI smoke that generated `sample_genre_heatmap.csv` and `sample_genre_heatmap.svg` twice from a seeded temporary database.
- Verified the second run matched the first byte-for-byte for both artifact files.
- Confirmed `git diff --check` stayed clean after the fixes.

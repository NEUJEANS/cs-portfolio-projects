# library-manager-sqlite borrower trend breakdown review log

Date: 2026-04-21

## Review pass 1, cohort SVG layout
- Inspected the first generated borrower SVG artifact for multi-borrower readability.
- Found issue: the legend used a fixed three-column modulo layout, so a fourth borrower landed on top of the first legend slot.
- Fix: switched the legend to a wrapped two-column layout with separate y offsets for later rows.

## Review pass 2, summary table spacing
- Rechecked the SVG after the legend fix and inspected the summary section near the bottom of the card.
- Found issue: the header row and first borrower row overlapped, and the table height was too loose for four rows inside the fixed SVG canvas.
- Fix: moved data rows below the header band and tightened row height so the full table stays within the card.

## Review pass 3, determinism and artifact hygiene
- Re-ran the borrower trend export twice with the same seeded sample data, explicit date range, and fixed `--generated-at` timestamp.
- Confirmed both CSV and SVG outputs were byte-identical across repeated runs with `cmp`.
- Ran `git diff --check` to catch whitespace or patch hygiene issues.
- No further fixes were needed after the deterministic rerun.

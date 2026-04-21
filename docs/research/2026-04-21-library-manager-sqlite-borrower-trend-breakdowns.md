# library-manager-sqlite borrower trend breakdown research

Date: 2026-04-21

## Goal
Add borrower-level trend breakdown exports on top of the existing circulation trend pack so the project tells a clearer multi-user story during portfolio demos.

## External references checked
1. MDN, `<title>` for SVG, fetched 2026-04-21 14:04 UTC
   - Use `<title>` for the short accessible name of the overall SVG and individual grouped chart regions.
   - Keep `<title>` as the first child for SVG 1.1 compatibility.
2. MDN, `<desc>` for SVG, fetched 2026-04-21 14:04 UTC
   - Use `<desc>` for longer chart explanations.
   - Pair it with `aria-describedby` IDs when multiple chart regions need non-visual context.
3. MDN, `<g>` for SVG, fetched 2026-04-21 14:04 UTC
   - Group related chart elements with `<g>` so panel-level labels and descriptions can be attached once and inherited by the contained shapes.

## Design takeaways
- Keep the original aggregate `trends` export unchanged.
  - It already tells the overall library story well.
  - Borrower breakdowns should be additive, not a replacement.
- Export borrower breakdowns as both CSV and SVG.
  - CSV is better for follow-up analysis and spreadsheet import.
  - SVG is better for committed artifacts and screenshots.
- Limit the SVG to top borrower cohorts.
  - A recruiter-friendly artifact should stay readable without a crowded legend.
  - Ranking borrowers by loans touching the selected range keeps the cohort choice stable and explainable.
- Show both trend lines and a summary table.
  - Trend lines answer who was active or overdue when.
  - The table answers total usage and peak load at a glance.

## Slice chosen
Add a new `borrower-trends` CLI export that emits:
- borrower/day CSV rows for the top borrower cohorts in the selected range
- an accessible SVG with cohort legend, active-loan trend panel, overdue-loan trend panel, and summary table
- deterministic sample artifacts committed under `docs/artifacts/library-manager-sqlite/`

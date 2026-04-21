# library-manager-sqlite trend exports research

Date: 2026-04-21

## Goal
Add chart-friendly circulation trend exports so the existing snapshot dashboard can grow into a small analytics pack that still works as a static portfolio artifact.

## External references checked
1. MDN, `<title>` for SVG, fetched 2026-04-21 13:45 UTC
   - Use `<title>` for short accessible names.
   - Keep `<title>` as the first child for SVG 1.1 compatibility.
   - If visible text already exists, `aria-labelledby` is a good way to connect it.
2. MDN, `<desc>` for SVG, fetched 2026-04-21 13:45 UTC
   - Use `<desc>` for a longer non-visual description.
   - Pair it with IDs so `aria-describedby` can reference it.

## Design takeaways
- Export both CSV and SVG, not just one format.
  - CSV is better for recruiter follow-up, spreadsheet import, and future charts.
  - SVG is better for committed, screenshot-friendly static artifacts.
- Prefer small multiples over one overloaded chart.
  - Active loans, overdue loans, checkouts, and returns do not share the same story or scale.
  - Separate panels stay readable without adding secondary axes.
- Keep the exports deterministic.
  - Accept explicit start/end dates.
  - Accept explicit generated timestamps for committed sample artifacts.
- Preserve historical correctness.
  - A trend export should answer, “what would the library have looked like on each day in this range?”
  - Future returns must not leak backward into earlier dates.

## Slice chosen
Add a `trends` CLI command that emits:
- daily CSV rows for chart-friendly metrics
- an accessible SVG small-multiples report
- deterministic sample artifacts committed under `docs/artifacts/library-manager-sqlite/`

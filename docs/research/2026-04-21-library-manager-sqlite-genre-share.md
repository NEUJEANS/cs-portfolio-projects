# Research — library-manager-sqlite genre share export — 2026-04-21

## Goal
Add a composition-first genre artifact that complements the existing heatmap. The heatmap already answers where the absolute load is; this slice should answer how the subject mix changes over time without hiding the daily denominator.

## External references checked
1. MDN, SVG `<title>`, fetched 2026-04-21 15:03 UTC
   - `<title>` provides the short accessible name for an SVG container or graphics element.
   - For SVG 1.1 compatibility it should appear as the first child of the parent.
2. MDN, SVG `<desc>`, fetched 2026-04-21 15:03 UTC
   - `<desc>` is the right place for a longer chart explanation.
   - Pairing it with `aria-describedby` keeps the static export understandable in assistive tech.
3. MDN, Colors and Luminance accessibility guide, fetched 2026-04-21 15:03 UTC
   - Luminance contrast matters more than hue alone for readability.
   - Distinct fills still need enough lightness separation and supporting text.
4. From Data to Viz, barplot overview, fetched 2026-04-21 15:09 UTC
   - Stacked bars are a reasonable way to show grouped composition while preserving a familiar bar-reading mental model.
   - They are especially useful when the goal is to compare how parts contribute within each category or time slice.

## Design takeaways
- Keep this as a new `genre-share` command instead of mutating `genre-heatmap` or `genre-trends`.
  - Existing artifact contracts stay stable.
  - Recruiters get a clearly different view: composition instead of intensity.
- Use normalized stacked daily bars for the SVG.
  - This makes each day comparable as a composition snapshot.
  - The separate total-active label above each bar preserves the missing denominator.
- Keep the CSV row model aligned with the existing genre exports.
  - One row per date/genre keeps spreadsheet follow-up easy.
  - Include `share_start` and `share_end` so the stack geometry is reproducible.
- Do not force a fake winner on tied-share days.
  - Unique dominance is useful summary context.
  - Ties should remain ties, not arbitrary leader assignments.

## Slice chosen
Add a `genre-share` CLI export that emits:
- date/genre CSV rows with active-loan counts, shares, stack bounds, and dominant-day flags
- an accessible SVG with normalized stacked bars, count labels above the bars, summary cards, and a compact genre table
- deterministic sample artifacts committed under `docs/artifacts/library-manager-sqlite/`

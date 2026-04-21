# Research — library-manager-sqlite genre heatmap — 2026-04-21

## Goal
Turn the genre analytics from separate cohort lines into a one-glance static artifact that still stays lightweight, deterministic, and easy to explain in interviews.

## External references checked
1. MDN, SVG `<title>`, fetched 2026-04-21 14:45 UTC
   - `<title>` provides the short accessible name for an SVG container or graphics element.
   - For SVG 1.1 compatibility, keep `<title>` as the first child of the parent element.
2. MDN, SVG `<desc>`, fetched 2026-04-21 14:45 UTC
   - `<desc>` is the right place for a longer non-visual explanation of the chart.
   - Pairing the outer SVG with `aria-describedby` keeps static portfolio exports easier to understand with assistive tech.
3. MDN, Accessibility guide on colors and luminance, fetched 2026-04-21 14:45 UTC
   - Luminance contrast matters more than hue alone for readable visual differentiation.
   - A simple light-to-dark sequential scale is safer for a compact heatmap than trying to encode too many meanings through color alone.

## Design takeaways
- Keep the existing `genre-trends` export for line-based cohort comparisons.
- Add a separate `genre-heatmap` export instead of mutating the old CSV schema.
  - This keeps downstream artifact consumers stable.
  - It also makes the new slice easy to demo as an additive upgrade.
- Encode cell intensity with active-loan counts and expose per-day share in tooltips and summary text.
  - Count is the fastest at-a-glance signal.
  - Share still matters, but it fits better as supporting context than as the only visual encoding.
- Include date totals above the grid and per-genre summary stats beside or below it.
  - That keeps the artifact understandable without opening the raw CSV.

## Slice chosen
Add a `genre-heatmap` CLI export that emits:
- genre/day CSV rows with active-loan counts, active-share values, and related daily metrics
- an accessible SVG heatmap with summary cards, readable row labels, and tooltip detail
- deterministic sample artifacts committed under `docs/artifacts/library-manager-sqlite/`

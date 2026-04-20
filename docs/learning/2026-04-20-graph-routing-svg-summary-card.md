# 2026-04-20 learning refresh — graph-routing SVG summary card

## Brief refresh takeaway
- For portfolio artifacts, SVG works best when the export is deterministic, text-first, and based on a stable `viewBox` instead of container-specific measurements.
- Accessibility details matter even for static portfolio graphics: an SVG should carry a short `<title>`/`<desc>` pair so screen readers and browser tooltips have meaningful context.
- Compact artifact design is a product decision as much as a rendering decision: summary metrics plus 2-3 changed-route highlights tell the story better than dumping the entire route table into the graphic.

## Self-test
1. Why prefer `viewBox`-driven layout for a committed SVG artifact?
   - Because it defines a stable logical canvas that scales cleanly without changing the underlying geometry or text positions.
2. Why add `preserveAspectRatio` to this export?
   - To make thumbnail and embed scaling predictable when the SVG is shown in containers with different dimensions.
3. Why keep the SVG deterministic instead of injecting timestamps or environment data?
   - So rerunning the same command produces the same committed artifact and avoids noisy diffs.
4. Why not cram every route diff into the card?
   - Because the SVG is meant to be a quick visual summary; the full Markdown/HTML artifacts remain the deeper audit surfaces.

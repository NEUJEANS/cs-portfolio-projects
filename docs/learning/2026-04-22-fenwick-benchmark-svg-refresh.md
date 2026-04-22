# 2026-04-22 fenwick benchmark SVG refresh

## Quick refresh
- SVG coordinates grow rightward and downward, so reserve vertical spacing up front instead of stacking with CSS assumptions.
- A fixed `viewBox` makes exported charts scale predictably across GitHub, browsers, and slide screenshots.
- Text alignment should be explicit with `text-anchor` when a label is right-aligned or centered.

## Self-test before/after implementation
- Make sure the renderer returns a complete `<svg ...>` document.
- Confirm the chart includes both strategies, throughput labels, and per-operation latency labels.
- Verify the CLI can write the SVG artifact beside the existing JSON, CSV, and Markdown outputs.

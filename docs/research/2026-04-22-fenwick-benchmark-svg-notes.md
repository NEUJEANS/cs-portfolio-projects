# 2026-04-22 fenwick benchmark SVG notes

## Brief external references
- MDN `viewBox`: use a fixed `min-x min-y width height` rectangle so the same SVG scales cleanly in README embeds and screenshots.
- MDN `text-anchor`: use explicit text anchoring for labels and footer alignment instead of relying on approximate spacing.

## Decision for this slice
- Keep the renderer fully stdlib and emit one standalone SVG file.
- Favor simple bars plus a few summary cards over heavier chart tooling so the benchmark stays reproducible in any Python environment.
- Show both throughput and average per-operation latency, because either metric alone would undersell the Fenwick vs segment-tree tradeoff.

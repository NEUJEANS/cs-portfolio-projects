# Learning refresh — 2026-04-18 — page replacement trace cards

## Quick refresher
- a good trace-summary card should answer two questions fast: **how local is this workload overall?** and **where do its phases shift?**
- reuse-distance buckets summarize locality distribution; colder buckets mean more first touches or long gaps between uses
- per-window unique-page counts show how much working-set pressure changes across the trace
- a phase hint becomes easier to trust visually when the chart highlights the boundary right where the page-set overlap drops

## Self-check
For `compiler-phase-shift` with window size `12`, the card should show:
- heavy `cold` first-touch pressure because the benchmark injects a long scan phase
- a per-window unique-page spike in the scan-heavy middle windows
- at least two phase-boundary hints, including one after reference `24`

## Why this slice matters
- the Markdown summary already explains the workload, but the SVG / HTML card makes it presentation-ready for portfolio pages and slides
- it reuses the simulator's existing metrics instead of inventing new heuristics, so the slice stays focused and low-risk
- it also keeps the project resumable for future work like working-set policies or side-by-side imported-trace comparisons

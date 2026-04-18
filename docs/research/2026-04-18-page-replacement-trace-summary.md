# Research note — 2026-04-18 — page-replacement trace summary

## Question
What is the most useful next vertical slice for `page-replacement-lab` after adding heavier benchmark traces but before implementing a full working-set replacement policy?

## Brief references checked
- Gemini web search summary on reference strings, working sets, phase detection, and reuse distance
- Stanford CS140 thrashing / working-set notes (`https://web.stanford.edu/~ouster/cgi-bin/cs140-winter12/lecture.php?topic=thrashing`)
- Rochester reuse-distance paper index (`https://www.cs.rochester.edu/u/cding/Documents/Publications/TR741.pdf`)

## Takeaways used for the implementation
- **Reuse distance** is a practical, interview-friendly metric: for each repeated page, count the distinct pages touched since its previous use.
- A **working-set window** can be approximated in a simulator with a fixed recent-reference window and a sliding unique-page count.
- **Phase shifts** do not need perfect offline segmentation for a portfolio tool; simple consecutive-window overlap is enough to flag scan-heavy transitions and hot-set changes.
- For a resumable CLI, fixed-size windows plus a configurable Jaccard threshold are more transparent than a hidden heuristic model.

## Implementation choice
- Add a `trace-summary` command instead of jumping straight to WSClock.
- Report reuse-distance buckets (`cold`, `1-2`, `3-5`, `6-9`, `10+`) plus min / median / p90 / max / average.
- Report sliding-window working-set size stats using a configurable `--window-size`.
- Flag **phase-boundary hints** when consecutive fixed windows overlap at or below a configurable Jaccard threshold.

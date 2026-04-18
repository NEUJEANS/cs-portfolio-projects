# Learning refresh — 2026-04-18 — page replacement trace summary

## Quick refresher
- **Reuse distance** counts how many distinct pages appear between two touches of the same page.
- Smaller reuse distances suggest stronger locality and usually friendlier behavior for recency-aware policies.
- A **working set** is the unique-page footprint inside a recent reference window.
- **Phase detection** can be approximated by comparing the page sets of neighboring windows and looking for sharp overlap drops.

## Self-check
Synthetic reference: `1 2 1 2 1 2 7 8 7 8 7 8`

With a window size of `6`, the summary should show:
- `4` first touches and `8` reuses
- two clear windows: `{1,2}` then `{7,8}`
- a phase-boundary hint after reference `6` because the consecutive window overlap is `0.0`

## Why this slice matters
- The simulator already measures fault counts; this slice explains **why** workloads behave differently.
- It adds a portfolio-ready story around locality analysis without committing to a heavier replacement-policy implementation yet.
- It sets up future slices like WSClock, aggregate comparisons, or richer custom-trace reporting.

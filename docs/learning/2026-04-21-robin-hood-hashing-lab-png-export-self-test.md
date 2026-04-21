# robin-hood-hashing-lab PNG export self-test

Date: 2026-04-21

## Quick refresh
- A full benchmark HTML page and a slide-ready PNG do not need to show the exact same amount of detail.
- For deterministic artifact bundles, PNG capture should reuse the same seeded HTML summary, then apply only presentation-level compaction.
- Browser-dependent CLI tests should still cover real capture when Chrome is available, but unit tests should mock command construction/rendering so the suite stays portable.

## Self-test
1. Why require `--html-out` when `--png-out` is requested?
   - Because the PNG is a screenshot companion to the HTML dashboard, not a separate renderer with different data plumbing.
2. Why use a compact screenshot mode instead of capturing the full dashboard as one giant PNG?
   - Because the full benchmark page is too tall for a practical slide or portfolio image. Compacting the capture keeps the PNG readable while the HTML artifact still preserves full detail.
3. What should stay configurable even after adding automatic PNG capture?
   - Browser binary discovery, viewport width/height, and capture wait budget, so real environments can still override defaults when needed.

# Extendible hashing lab PNG capture self-test — 2026-04-21

- Goal: add a resumable PNG helper without introducing a second benchmark renderer or a frontend/browser-automation dependency tree.
- Refresher: the HTML dashboard is already the benchmark source of truth for portfolio browsing, so the PNG helper should sit on top of that artifact instead of forking the presentation logic.
- Refresher: for screenshot helpers, viewport sizing matters more than image post-processing; an oversized but stable capture is better than clipping the lower scenario cards.

## Self-check notes
1. Why should `--png-out` require `--html-out`?
   - Because the raster asset is intentionally captured from the generated HTML dashboard, and the CLI should make that dependency obvious instead of silently rendering through a different path.
2. Why use headless Chrome/Chromium directly?
   - It keeps the feature dependency-light, matches an existing repo pattern, and works with self-contained `file://` dashboards.
3. What should be tested beyond the happy path?
   - command construction, parser rejection when `--png-out` is used without `--html-out`, and an end-to-end CLI smoke path when Chrome is available.
4. What is the next likely follow-up after this slice?
   - a smaller visualization thumbnail-strip or PNG path for the split/merge walkthrough so the non-benchmark artifact story is just as easy to embed.

# Extendible hashing lab visualization PNG self-test — 2026-04-21

- Goal: extend the existing visualization workflow with a screenshot-friendly PNG export without forking the rendering logic or adding a heavier browser-automation dependency.
- Refresher: the HTML visualization page is already the source of truth for the full split/merge walkthrough, so PNG capture should sit on top of that artifact.
- Refresher: multi-step visualization pages can be much taller than dashboards, so height measurement + a safe heuristic fallback matter more than exact pixel-perfect tuning.

## Self-check notes
1. Why should `visualize --png-out` require `--html-out`?
   - Because the PNG is intentionally captured from the generated HTML visualization, and the CLI should make that dependency explicit.
2. Why reuse the benchmark screenshot helper pattern instead of adding a separate renderer?
   - It keeps the slice dependency-light, consistent, and easier to maintain across projects.
3. What should be tested beyond the happy path?
   - parser rejection when `--png-out` is used without `--html-out`, command construction, missing-HTML failure, full CLI behavior when Chrome is available, and deterministic reruns against committed artifacts.
4. What is the likely next follow-up after this slice?
   - an overview landing page that bundles the sample/delete-heavy HTML, PNG, and thumbnail-strip artifacts into one recruiter-friendly entry point.

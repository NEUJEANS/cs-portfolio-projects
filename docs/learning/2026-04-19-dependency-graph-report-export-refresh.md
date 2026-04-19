# Dependency Graph Planner Refresh — 2026-04-19 report export slice

## Short refresh
- GitHub will render Mermaid only when the diagram is inside a fenced `mermaid` block, so raw `.mmd` is useful source material but a Markdown wrapper is better for browsing.
- A report artifact is easier to review if it reuses the planner's existing deterministic order, layer, and timing data rather than recalculating anything separately.
- Relative links matter for committed artifact bundles because the report may live in a different directory than the generated diagrams.
- Report-only flags should fail fast on other commands so accidental CLI misuse does not silently create confusing files.

## Self-test
1. Why generate report sections from the existing `PlanResult` instead of rebuilding timing logic?
   - To keep the artifact deterministic and avoid divergence between terminal output and exported reports.
2. Why emit a Markdown Mermaid wrapper in addition to a raw `.mmd` file?
   - GitHub previews the fenced Markdown version directly, which is better for recruiters and README browsing.
3. Why prefer relative links inside the report?
   - They keep the artifact bundle portable across repo directories and still work after commit/push.

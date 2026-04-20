# Dependency graph planner report-dashboard refresh — 2026-04-20

## Short refresh
- Deterministic static artifacts should avoid live timestamps so rerunning the same command only changes output when the underlying schedule/report data changes.
- Schedule SVGs should be keyed by stable schedule identity (`worker_limit` + optional strategy), not by run time, so committed artifacts remain predictable.
- A report-level HTML dashboard can stay lightweight if it links to existing Markdown, Mermaid, DOT, JSON, and SVG artifacts instead of duplicating the whole report body.
- Relative links must be computed from the file being written, not from the process working directory.

## Self-test
1. Why should the report dashboard filename derive from the report output stem instead of only the graph stem?
   - Because the same manifest can produce multiple report variants, and each variant needs a non-colliding dashboard artifact.
2. Why are schedule SVGs a better GitHub-facing companion than raw JSON alone?
   - GitHub previews SVG directly, so reviewers can understand worker timelines without downloading or parsing JSON.
3. What makes the dashboard artifact resumable-friendly?
   - Stable filenames plus deterministic content let a later run regenerate or extend the same artifact set without manual cleanup.

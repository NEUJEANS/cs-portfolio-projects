# Mini MapReduce review log — structured benchmark annotations slice

Date: 2026-04-17

## Review pass 1 — artifact portability audit
- Read through the new benchmark JSON/CSV/Markdown/HTML flow with an eye toward committed portfolio artifacts.
- Found one publishability issue: plugin-backed `run` and `benchmark` payloads still emitted absolute local plugin paths, which would leak workspace-specific paths into committed artifacts.
- Fix applied: normalized plugin references in `JobResult`, `BenchmarkResult`, and benchmark heatmap rows to repo-relative paths via `plugin_display_path(...)`.
- Follow-up fix: updated README output examples and project/repo tests to assert the repo-relative contract explicitly.

## Review pass 2 — generated artifact audit
- Ran a real plugin benchmark export to `docs/artifacts/mini-mapreduce/2026-04-17-structured-annotations-*`.
- Verified the JSON artifact includes `benchmark_note_annotations`, severity labels, hotspot keys, and the repo-relative plugin path `projects/mini-mapreduce-lab/plugins_average_score.py`.
- Verified the Markdown and HTML artifacts render the new `Structured benchmark annotations` section cleanly with the expected `Demo-day crunch hotspot` callout.
- No additional fixes needed.

## Review pass 3 — CLI smoke validation
- Ran a fresh CLI smoke test for both `run plugin` and `benchmark --job plugin` against temporary files.
- Verified both payloads now emit the repo-relative plugin path and that the balanced `project-week` benchmark exposes the `Studio squad baseline` annotation block.
- Smoke result: `smoke-ok`.

# Dependency graph planner review — 2026-04-20 worker-limited report slice

## Pass 1 — artifact completeness
- Reviewed the new worker-limited report flow against the README and committed artifacts.
- Found a gap: the report listed a committed `sample_graph_single_worker_schedule.json` artifact, but the `report` workflow only wrote Mermaid/DOT companions.
- Fix applied: taught `write_report_supporting_artifacts(...)` to emit a deterministic worker-limited schedule JSON file when `--worker-limit` is present and to surface that path through the returned artifact map.

## Pass 2 — wording and link coverage
- Reviewed the generated report text and README examples for recruiter-facing clarity.
- Found two issues:
  1. summary wording rendered awkwardly as `1 workers`
  2. the linked-artifacts section still omitted the worker-limited schedule JSON companion
- Fix applied: added singular/plural helper logic for worker wording and extended report artifact link generation so Markdown reports include the schedule JSON link with a repo-relative path.

## Pass 3 — regression + determinism verification
- Reviewed tests, regenerated sample artifacts, and checked reproducibility of the committed output bundle.
- Found a stale-output issue after the code change: the committed sample single-worker report had to be regenerated so its linked-artifacts block matched the updated exporter.
- Fix applied: reran the report command for the committed artifact set, then double-exported to `/tmp/dependency-graph-planner-review-a` and `/tmp/dependency-graph-planner-review-b` and confirmed matching SHA-256 hashes for both `report.md` and `sample_graph_single_worker_schedule.json`.

## Result
- Worker-limited reports now emit and link the schedule JSON companion artifact automatically.
- Recruiter-facing wording reads cleanly for singular worker counts.
- Tests and deterministic artifact regeneration passed after the fixes.

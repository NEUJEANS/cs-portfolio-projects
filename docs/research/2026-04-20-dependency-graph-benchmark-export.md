# Dependency graph planner benchmark export slice research — 2026-04-20

## Brief research
- No external web research was needed for this slice because the benchmark runner, report renderer, and artifact-writing helpers already existed locally.
- The missing portfolio value was not a new algorithm; it was a machine-friendly export layer so the benchmark suite can feed downstream plots, notebooks, or lightweight dashboards without copy/pasting Markdown tables.
- Python's stdlib `json` + `csv.DictWriter` are sufficient here because the export shapes are flat, deterministic, and already derived from in-memory benchmark result objects.

## Slice decision
Finish the unfinished local benchmark-export slice by:
- adding first-class `--benchmark-json-out`, `--benchmark-aggregate-csv-out`, and `--benchmark-strategy-csv-out` outputs
- keeping graph/source labels repo-relative so committed artifacts stay readable on GitHub
- committing the generated JSON/CSV artifacts beside the existing Markdown report
- tightening CLI validation coverage so benchmark-only export flags fail clearly on non-benchmark commands

Why this is the right next slice:
- it completes the exact checklist item that was still open in `projects/dependency-graph-planner/CHECKLIST.md`
- it turns the benchmark suite into something reusable for later plotting/dashboard slices
- it stays resumable because future dashboard work can consume the committed JSON/CSV snapshots directly

# 2026-04-21 consistent-hashing benchmark export research note

## Goal
Upgrade `consistent-hashing-lab` so its virtual-node benchmark can produce portfolio-ready artifacts directly instead of requiring manual copy/paste from JSON.

## Research summary
- For student portfolio benchmarking, JSON is great for correctness and scripting, but CSV and short Markdown reports are better for spreadsheets, README snippets, and recruiter-facing writeups.
- Consistent-hashing benchmark exports should stay deterministic and reuse the exact measured series so charts and narrative summaries cannot drift from the raw benchmark output.
- The most useful flat export fields are the tested virtual-node count, balance metrics, and optional topology-change churn metrics, because those are the main comparison axes for this lab.

## Design chosen for this slice
- keep JSON as the primary CLI stdout payload
- add optional `--csv-out` for chart-ready flat rows
- add optional `--markdown-out` for a short benchmark report with a summary table and takeaways
- save one reproducible sample export set under `docs/artifacts/consistent-hashing-lab/`

## Notes
A web search was attempted for this slice, but the search provider returned a quota error, so the design falls back to standard benchmark-reporting best practices already consistent with the repo's existing artifact workflow.

# Learning refresh — 2026-04-18 — log-analyzer facet slice

## Python/tool refresh
- `parse_extra_fields(...)` already preserves unknown named fields, so facet support can stay surgical: keep parsing in one place and add reporting/CSV layers on top.
- Existing latency summarizers already work for `(path, facet_values)` tuple keys, which avoids duplicating percentile logic.
- CSV exports should carry explicit metadata columns (`facet_label`, `facet_<field>`, filters, window bounds) so downstream notebook/Sheets use stays trivial.
- Facet support should not pollute unrelated outputs: time-bucket facet sections only make sense when `--time-bucket` is active.

## Self-test plan
- confirm named fields survive parsing and missing facet values become `(missing)`
- confirm `analyze_lines(...)` exposes request/upstream hotspot facet breakdowns plus time-bucket facet breakdowns
- confirm text output mentions facet sections without printing bogus time-bucket facet headings when bucketing is disabled
- confirm summary CSV and dedicated facet CSV exports include the right metadata columns/rows
- confirm CLI validation rejects invalid facet names and facet-export misuse
- confirm the existing non-facet latency/time-window behavior remains unchanged
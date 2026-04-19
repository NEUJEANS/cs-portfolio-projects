# Log Analyzer facet ranking refresh — 2026-04-19 02:05 UTC

## What I refreshed
- Reused the project’s existing `facet_label` / `facet_<field>` export pattern instead of inventing a different schema for ranked tables.
- Kept the new slice focused on top IPs and top paths only so the feature stays portfolio-useful without bloating every ranking surface at once.
- Planned the new summaries to sort within each facet by count first, then key, matching the repo’s current deterministic-report style.

## Self-test plan before coding
- `analyze_lines(...)` should expose deterministic `top_ips_by_facet` and `top_paths_by_facet` rows when `--facet-field` values are supplied.
- text output should mention the facet-aware ranking sections only when faceting is active.
- JSON output should include the new facet-ranking arrays.
- `--top-ip-facet-csv` / `--top-path-facet-csv` should fail fast without `--facet-field` and should emit self-describing CSVs with `facet_label`, `facet_<field>`, `rank`, `key`, and `count` columns.

## Review findings after implementation
- Ordering facet groups purely by label made lower-traffic facets appear before busier deploy/release labels in the committed sample outputs, so the shipped helper now sorts facet groups by total request volume first and uses the label only as a deterministic tiebreaker.
- CSV coverage now also locks `window_start` / `window_end` metadata so filtered exports stay spreadsheet-friendly and self-describing.

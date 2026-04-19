# Log Analyzer referrer/user-agent facet refresh — 2026-04-19 02:54 UTC

## What I refreshed
- Reused the existing `summarize_top_counts_by_facet(...)` and facet CSV writer so the new slice stays schema-compatible with the earlier IP/path facet exports.
- Refreshed the expected combined-log shape for referrer and user-agent parsing before touching the sample artifacts.
- Kept the slice focused on surfacing richer ranking outputs from already-parsed fields instead of adding a second faceting system.

## Self-test plan before publish
- facet-aware JSON output should now expose `top_referrers_by_facet` and `top_user_agents_by_facet` alongside the existing IP/path arrays
- text output should only show the new ranking sections when faceting is active
- `--top-referrer-facet-csv` and `--top-user-agent-facet-csv` should emit the same `facet_label`, `facet_<field>`, `rank`, `count`, and time-window metadata pattern as the earlier facet ranking CSVs
- committed sample artifacts should be reproducible from `docs/artifacts/log-analyzer/facet-ranking-sample.log` without any manual post-processing

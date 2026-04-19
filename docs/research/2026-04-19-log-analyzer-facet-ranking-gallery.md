# Research — 2026-04-19 — log-analyzer facet ranking gallery

## Goal
Turn the existing per-facet ranking output into a browser-friendly artifact so referrer/user-agent heavy release reviews can show grouped evidence without opening multiple CSV files.

## Quick findings
- Datadog's Top List widget docs emphasize ranked dimensions/tags as a first-class dashboard view, including relative/absolute display modes and context links to deeper investigation pages.
- Grafana's table visualization docs emphasize tables as a flexible way to show logs/metrics/traces together, with filtering and data-link style workflows for drill-down.
- That combination maps well to this project: the analyzer already has ranking CSVs, but it lacked a single static page that grouped per-facet ranked tables and linked them to comparison-card artifacts.

## Sources checked
- Datadog docs — Top List Widget: https://docs.datadoghq.com/dashboards/widgets/top_list/
- Grafana docs — Table visualization: https://grafana.com/docs/grafana/latest/panels-visualizations/visualizations/table/

## Slice decision
Implement a dedicated `--facet-ranking-gallery-html` export with repeatable `--facet-ranking-gallery-link` support so the existing per-facet top-IP/top-path/top-referrer/top-user-agent output can be bundled into one portable HTML page.

## Why this slice
It strengthens the portfolio story: students can show one polished artifact that mirrors real observability review flows (ranked slices + drill-down links) while still keeping the underlying CSVs and comparison cards reproducible from the CLI.
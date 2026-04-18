# Research — 2026-04-18 — log-analyzer comparison-card artifacts

## Goal
Extend `projects/log-analyzer` with portfolio-ready SVG/HTML comparison cards built from the existing `--facet-compare-*` output so release-review screenshots do not require a spreadsheet or external charting tool.

## Quick findings
- Brief official-doc research shows that observability tools treat deploy/release markers and version comparisons as first-class context, not as an afterthought.
- Grafana annotations docs emphasize event markers, tags, and dashboard-level annotation queries so release/deploy context stays visible directly on charts.
- Datadog deployment-tracking docs emphasize comparing request, error, and latency behavior by `version` tag on service pages and dashboards.
- That maps well to this project’s existing `env` / `release` / `region` facet comparisons: the missing portfolio piece is a self-contained artifact that turns those deltas into a slide/browser-friendly card.

## Sources checked
- Grafana docs — `Annotate visualizations`: https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/annotate-visualizations/
- Datadog docs — `Deployment Tracking`: https://docs.datadoghq.com/tracing/services/deployment_tracking/

## Slice decision
Implement dedicated comparison-card exports that:
1. reuse the existing facet-comparison summary + aligned bucket data
2. surface request/error/latency deltas at a glance in a standalone SVG card
3. provide an HTML companion with the card plus exact summary and per-bucket tables
4. generate a committed example artifact bundle for README/portfolio screenshots

## Why this slice
It upgrades the project from “CLI + CSV analysis” into a stronger portfolio story: a student can show realistic release-review evidence directly inside GitHub Pages, slides, or README screenshots without needing Grafana/Datadog accounts or a follow-up notebook step.

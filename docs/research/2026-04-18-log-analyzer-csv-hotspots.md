# Research — 2026-04-18 — log-analyzer CSV + hotspot slice

## Goal
Choose a small but meaningful observability-oriented upgrade for `projects/log-analyzer`.

## Quick findings
- NGINX logging guidance emphasizes that access logs can carry end-to-end request latency (`$request_time`) and upstream latency fields, which makes request-path-level performance analysis a realistic observability task rather than a toy parser exercise.
- Performance-monitoring writeups commonly group latency by endpoint/path so slow routes stand out quickly during incident review or optimization work.
- For portfolio/demo workflows, a flat CSV export is valuable because it drops directly into Sheets/Excel/chart tools for screenshots, charts, and quick comparisons without extra scripting.

## Sources checked
- NGINX Admin Guide — Logging: https://docs.nginx.com/nginx/admin-guide/monitoring/logging/
- NGINX blog — Using NGINX Logging for Application Performance Monitoring: https://blog.nginx.org/blog/using-nginx-logging-for-application-performance-monitoring

## Slice decision
Implement two linked upgrades:
1. spreadsheet-friendly CSV exports for summary metrics and ranked counters
2. per-path latency hotspot summaries so slow endpoints show up directly in text/JSON output and can also be exported for charts

## Why this slice
It strengthens the project along a real ops/observability axis without changing the tool's standard-library-only footprint.

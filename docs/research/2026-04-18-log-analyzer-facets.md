# Research — 2026-04-18 — log-analyzer deployment/environment facets

## Goal
Extend `projects/log-analyzer` so richer access-log lines with extra named `key=value` fields can be split by deployment/environment metadata such as `env=prod`, `region=us-east-1`, or `release=2026.04`.

## Quick findings
- Brief web research against official Nginx logging docs confirmed that `log_format` can include arbitrary variables, not just the classic common/combined fields.
- That means real teams often add deploy, shard, region, release, or upstream identifiers directly into access logs beside timing fields.
- The project already parses named timing fields like `request_time=` and `upstream_response_time=`. The next portfolio-friendly slice is to preserve the rest of those named fields and expose them in trend/hotspot outputs.

## Sources checked
- Official Nginx `ngx_http_log_module` / `log_format` docs (via grounded web-search recap pointing to `nginx.org`)
- Nginx logging admin-guide references on custom access-log variables

## Slice decision
Implement repeatable `--facet-field` support that:
1. preserves named `key=value` fields from the parsed log tail
2. adds per-facet hotspot breakdowns for request and upstream latency
3. adds per-facet time-bucket breakdowns plus dedicated CSV exports
4. keeps missing facet values explicit as `(missing)` so spreadsheet/chart output stays self-describing

## Why this slice
This turns the analyzer from a single-stream incident summary into a richer observability portfolio project: students can now compare prod vs staging, region vs region, or release vs release using the same raw logs and export screenshot-ready data without external tooling.
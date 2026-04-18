# Research — 2026-04-18 — log-analyzer Nginx timing fields slice

## Goal
Make `projects/log-analyzer` accept more realistic Nginx performance-monitoring log lines without abandoning the existing common/combined-log parser shape.

## Quick findings
- Official Nginx docs describe `$request_time` as request processing time in seconds with millisecond resolution, so it is a good source for the primary end-to-end latency summary.
- Official upstream-module docs describe `$upstream_response_time` in the same units and note that multiple upstream attempts can appear as comma/colon-separated values.
- That multi-value behavior means a portfolio-friendly analyzer should not choke on retry chains; it should ingest them deliberately and document how it aggregates them.

## Sources checked
- Nginx core module embedded variables: https://nginx.org/en/docs/http/ngx_http_core_module.html
- Nginx upstream module embedded variables: https://nginx.org/en/docs/http/ngx_http_upstream_module.html
- Nginx blog — application performance monitoring via access logs: https://blog.nginx.org/blog/using-nginx-logging-for-application-performance-monitoring

## Slice decision
Implement support for trailing named timing fields after the existing access-log line parser:
1. treat `request_time=` as the primary request-latency source when present
2. parse `upstream_response_time=` into a separate upstream-latency summary
3. sum multi-attempt upstream timing values per request so retries stay visible in the report and CSV export

## Why this slice
It upgrades the project from a generic access-log parser into a more realistic observability demo while keeping the standard-library-only footprint and the current CLI surface area.

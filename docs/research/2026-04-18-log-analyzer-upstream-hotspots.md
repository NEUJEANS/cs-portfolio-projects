# Research — 2026-04-18 — log-analyzer upstream hotspot slice

## Goal
Extend `projects/log-analyzer` so Nginx `upstream_response_time=` data is visible per request path, not only in one global summary.

## Quick findings
- Official Nginx docs describe `$upstream_response_time` as upstream response time in seconds with millisecond resolution.
- When multiple upstream attempts happen, Nginx emits multiple values; commas separate repeated upstream attempts within a group and colons can appear when the request flows across upstream groups/internal redirects.
- Because the analyzer already aggregates retry chains per request, the next portfolio-friendly slice is to surface those per-request aggregates by path so slow dependencies stand out by endpoint.

## Sources checked
- Nginx upstream module variables: https://nginx.org/en/docs/http/ngx_http_upstream_module.html
- Nginx blog — application performance monitoring via access logs: https://blog.nginx.org/blog/using-nginx-logging-for-application-performance-monitoring
- Grounded web search recap confirming comma/colon multi-value semantics for `$upstream_response_time`

## Slice decision
Implement per-path upstream hotspot reporting with the same percentile schema already used for request latency:
1. collect `upstream_response_time=` aggregates by request path
2. expose them in JSON/text output as `upstream_path_latency_breakdown`
3. add a dedicated CSV export so spreadsheet/chart workflows can compare app latency vs downstream latency

## Why this slice
It closes the biggest gap left by the previous Nginx timing-fields slice: users can now tell whether `/api/report` is slow because the app path itself is expensive, because an upstream dependency is slow, or both.
# log-analyzer

## Overview
Analyze common, combined, and latency-augmented web access logs from the command line with time-window slicing, minute/hour trend bucketing, per-status, per-method, top-IP, top-path, referrer, user-agent, request-latency, upstream-latency, and incident-style per-path hotspot drill-downs.

## Why it is portfolio-worthy
- parses realistic common and combined access-log lines instead of doing loose substring counting
- surfaces operational metrics that resemble real observability and traffic-analysis tasks
- includes both human-readable and machine-friendly outputs for scripting, spreadsheets, and chart pipelines
- highlights slow endpoints directly with per-path request and upstream latency hotspot summaries
- supports status/method-filtered hotspot drill-downs plus bounded time-window analysis for incident-response style investigations
- exports minute/hour trend buckets so students can turn raw logs into screenshot-ready latency and error-rate stories
- handles malformed lines, missing byte counts, and optional latency fields safely

## Stack
- Python 3
- standard library only

## Features
- parses common log lines like `IP - - [time] "METHOD /path HTTP/1.1" 200 123`
- also parses combined log tails with referrer and user-agent fields
- optionally parses a trailing response-time token and normalizes it to milliseconds
- parses Nginx-style named timing fields such as `request_time=` and `upstream_response_time=` when they appear after the access-log line
- counts requests by HTTP status code and request method
- reports top client IPs, paths, referrers, and user agents
- tracks total bytes, average bytes per request, malformed line count, request latency percentiles, and upstream latency percentiles when present
- supports inclusive `--window-start` / `--window-end` filters so larger logs can be narrowed to the exact burst, deploy, or outage window under investigation
- surfaces per-path request-latency hotspots ordered by average latency
- surfaces per-path upstream latency hotspots when `upstream_response_time=` data is present, so slow dependencies stand out by endpoint
- supports incident-style hotspot filters via `--hotspot-status` and `--hotspot-method` without changing the global summary metrics inside the selected time window
- supports minute/hour trend bucketing via `--time-bucket` plus chart-friendly `--time-bucket-csv` exports
- supports `--top`, `--latency-paths`, `--summary-csv`, `--path-latency-csv`, `--upstream-path-latency-csv`, `--time-bucket`, `--time-bucket-csv`, `--hotspot-status`, `--hotspot-method`, `--window-start`, `--window-end`, and `--format text|json`

## Usage
```bash
python3 log_analyzer.py access.log
python3 log_analyzer.py access.log --top 5
python3 log_analyzer.py access.log --format json
python3 log_analyzer.py access.log --summary-csv summary.csv --path-latency-csv hotspots.csv
python3 log_analyzer.py access.log --path-latency-csv request-hotspots.csv --upstream-path-latency-csv upstream-hotspots.csv
python3 log_analyzer.py access.log --time-bucket minute --format json
python3 log_analyzer.py access.log --time-bucket minute --time-bucket-csv minute-trends.csv --summary-csv summary.csv
python3 log_analyzer.py access.log --hotspot-status 500 --hotspot-status 502 --hotspot-method POST --format json
python3 log_analyzer.py access.log --window-start 2026-04-18T09:00:00Z --window-end 2026-04-18T10:00:00Z --time-bucket hour --format json
```

The parser accepts:
- common logs: `IP - - [time] "METHOD /path HTTP/1.1" 200 123`
- combined logs: `... 200 123 "https://referrer.example/" "Mozilla/5.0"`
- optional latency tails after either format:
  - decimal values are treated as seconds (for example `0.245` -> `245.0 ms`)
  - integer values are treated as microseconds (for example `12345` -> `12.345 ms`)
- optional Nginx-style named timing fields after either format:
  - `request_time=0.245` becomes the primary request latency summary input
  - `upstream_response_time=0.201` feeds the upstream latency summary
  - multi-attempt upstream values such as `upstream_response_time=0.050, 0.125:0.075` are summed per request so retries stay visible in totals

## Time-window filtering
Use `--window-start` and/or `--window-end` when you want to isolate a particular incident window, deploy interval, or traffic burst before calculating totals, percentiles, and hotspot tables.

Accepted timestamp formats:
- ISO-8601 / RFC 3339 style values such as `2026-04-18T09:00:00Z` or `2026-04-18T09:00:00+00:00`
- naive ISO values such as `2026-04-18T09:00:00` (treated as UTC)
- common-log timestamps such as `18/Apr/2026:09:00:00 +0000`

Behavior:
- bounds are inclusive
- entries outside the active window are excluded from the analyzed dataset
- text output prints the active window plus matched/excluded request counts
- JSON output includes a `time_window` object
- summary CSV exports add `time_window_*` rows and hotspot CSV exports add `window_start` / `window_end` columns so downstream charts stay self-describing

Examples:
- `--window-start 2026-04-18T09:00:00Z` keeps only entries at or after `09:00 UTC`
- `--window-end 2026-04-18T10:00:00Z` keeps only entries at or before `10:00 UTC`
- combine both flags to isolate the exact 5-minute outage window, then layer `--hotspot-status 500 --hotspot-method POST` on top for a narrower drill-down

## Time-bucket trends
Use `--time-bucket minute` or `--time-bucket hour` when you want the matched requests summarized into chart-friendly trend buckets after any active `--window-start` / `--window-end` filtering is applied.

Each bucket includes:
- `bucket_start` / `bucket_end`
- request and error counts plus `error_rate_pct`
- the most frequent path inside the bucket
- request-latency sample count plus average / p95 / max latency
- upstream-latency sample count plus average / p95 / max latency when `upstream_response_time=` data is present

Outputs:
- text mode prints a `Time bucket trends (...)` section for quick incident reviews
- JSON mode includes `time_bucketing` metadata plus a `time_buckets` array
- summary CSV exports add `time_bucket_granularity` and `time_bucket_count` rows
- `--time-bucket-csv` writes one row per bucket for spreadsheet/chart workflows and requires `--time-bucket`

Examples:
- `--time-bucket minute` highlights minute-by-minute spikes during a short outage
- `--window-start 2026-04-18T09:00:00Z --window-end 2026-04-18T10:00:00Z --time-bucket hour` compares hourly trend buckets inside a bounded incident window
- `--time-bucket minute --time-bucket-csv minute-trends.csv` exports chart-ready bucket rows for Sheets or notebooks

## Hotspot drill-downs
Use `--hotspot-status` and `--hotspot-method` when you want the per-path hotspot sections and CSV exports to focus on a particular incident slice while keeping the top-level totals and percentile summaries global **within the currently selected time window**.

Examples:
- `--hotspot-status 500 --hotspot-status 502` isolates failing paths in the hotspot tables/exports
- `--hotspot-method POST` focuses the hotspot tables/exports on mutating requests
- combine both flags to highlight slow failing write endpoints without losing the overall traffic summary for the selected time window

When filters are active:
- text output annotates the hotspot section headings with the active filters
- JSON output includes a `hotspot_filters` object
- hotspot CSV exports add `status_filter` and `method_filter` columns so downstream charts stay self-describing

## CSV exports
Use `--summary-csv` when you want a flat spreadsheet-friendly export of totals, ranked counters, and latency summary metrics.

Example columns:
- `section` — which summary family the row belongs to (`summary`, `status_counts`, `top_paths`, `latency_summary`, `upstream_latency_summary`, ...)
- `metric` — named metric for scalar values
- `key` — status code, path, referrer, or user-agent value
- `rank` — rank for top lists
- `count` — count for counter-based rows
- `value` — scalar metric value

Use `--path-latency-csv` to export one row per request-latency hotspot path with these columns:
- `path`
- `count`
- `average_ms`
- `p50_ms`
- `p95_ms`
- `p99_ms`
- `max_ms`
- `status_filter`
- `method_filter`
- `window_start`
- `window_end`

Use `--upstream-path-latency-csv` to export the same schema for `upstream_response_time=`-backed hotspots only. This makes it easy to show which endpoints are slow because of downstream services versus app-side processing. The filter/window columns stay blank when no hotspot or time-window flags are active.

Use `--time-bucket-csv` together with `--time-bucket` to export one row per bucket with these columns:
- `granularity`
- `bucket_start`
- `bucket_end`
- `request_count`
- `error_count`
- `error_rate_pct`
- `top_path`
- `top_path_count`
- `latency_sample_count`
- `average_latency_ms`
- `p95_latency_ms`
- `max_latency_ms`
- `upstream_latency_sample_count`
- `average_upstream_latency_ms`
- `p95_upstream_latency_ms`
- `max_upstream_latency_ms`
- `window_start`
- `window_end`

This makes it easy to drop a run into Sheets, Numbers, Excel, or plotting notebooks for portfolio screenshots and follow-up analysis.

## Sample text output
```text
Log Analysis Summary
Total requests: 42
Invalid lines: 1
Total bytes sent: 18024
Average bytes/request: 429.14
Time window:
  Start: 2026-04-18T09:00:00+00:00
  End: 2026-04-18T10:00:00+00:00
  Matched requests: 42
  Excluded requests: 18
Time bucket trends (hour):
  2026-04-18T09:00:00+00:00 -> requests=42, errors=7 (16.667%), top_path=/api/export (8)
    request latency: samples=40, avg=18.225, p95=52.8, max=109.0
    upstream latency: samples=28, avg=13.417, p95=36.5, max=51.0
Status counts:
  200: 35
  404: 5
  500: 2
Method counts:
  GET: 38
  POST: 4
Top IPs:
  10.0.0.1: 10
Top paths:
  /: 12
Top referrers:
  https://portfolio.example/blog: 7
Top user agents:
  Mozilla/5.0: 14
Latency summary (ms):
  Count: 40
  Average: 18.225
  p50: 11.4
  p95: 52.8
  p99: 88.3
  Max: 109.0
Upstream latency summary (ms):
  Count: 28
  Average: 13.417
  p50: 10.2
  p95: 36.5
  p99: 44.9
  Max: 51.0
Per-path latency hotspots (ms): (filters: status=500,502; method=POST)
  /api/export: count=5, avg=91.3, p95=118.1, max=121.0
Per-path upstream latency hotspots (ms): (filters: status=500,502; method=POST)
  /api/export: count=5, avg=73.6, p95=99.0, max=101.4
```

## Test
```bash
python3 -m unittest discover -s projects/log-analyzer -p "test_*.py"
```

## Future Improvements
- optionally group hotspot drill-down exports by deployment or environment labels when those appear in richer custom log formats
- add deployment/environment facets to time-bucket exports so trend charts can be split by shard, release, or region

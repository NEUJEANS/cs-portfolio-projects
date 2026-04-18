# log-analyzer

## Overview
Analyze common, combined, and latency-augmented web access logs from the command line with per-status, per-method, top-IP, top-path, referrer, user-agent, request-latency, and upstream-latency summaries.

## Why it is portfolio-worthy
- parses realistic common and combined access-log lines instead of doing loose substring counting
- surfaces operational metrics that resemble real observability and traffic-analysis tasks
- includes both human-readable and machine-friendly outputs for scripting and spreadsheet workflows
- highlights slow endpoints directly with per-path latency hotspot summaries
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
- surfaces per-path request-latency hotspots ordered by average latency
- supports `--top`, `--latency-paths`, `--summary-csv`, `--path-latency-csv`, and `--format text|json`

## Usage
```bash
python3 log_analyzer.py access.log
python3 log_analyzer.py access.log --top 5
python3 log_analyzer.py access.log --format json
python3 log_analyzer.py access.log --summary-csv summary.csv --path-latency-csv hotspots.csv
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

## CSV exports
Use `--summary-csv` when you want a flat spreadsheet-friendly export of totals, ranked counters, and latency summary metrics.

Example columns:
- `section` — which summary family the row belongs to (`summary`, `status_counts`, `top_paths`, `latency_summary`, `upstream_latency_summary`, ...)
- `metric` — named metric for scalar values
- `key` — status code, path, referrer, or user-agent value
- `rank` — rank for top lists
- `count` — count for counter-based rows
- `value` — scalar metric value

Use `--path-latency-csv` to export one row per hotspot path with these columns:
- `path`
- `count`
- `average_ms`
- `p50_ms`
- `p95_ms`
- `p99_ms`
- `max_ms`

This makes it easy to drop a run into Sheets, Numbers, Excel, or plotting notebooks for portfolio screenshots and follow-up analysis.

## Sample text output
```text
Log Analysis Summary
Total requests: 42
Invalid lines: 1
Total bytes sent: 18024
Average bytes/request: 429.14
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
Per-path latency hotspots (ms):
  /api/export: count=5, avg=91.3, p95=118.1, max=121.0
  /dashboard: count=8, avg=44.8, p95=58.7, max=63.2
```

## Test
```bash
python3 -m unittest discover -s projects/log-analyzer -p "test_*.py"
```

## Future Improvements
- add time-window or status-filter options for larger operational datasets
- optionally surface per-path upstream latency hotspots when `upstream_response_time=` data is available

# log-analyzer

## Overview
Analyze common, combined, and latency-augmented web access logs from the command line with per-status, per-method, top-IP, top-path, referrer, user-agent, and latency summaries.

## Why it is portfolio-worthy
- parses realistic common and combined access-log lines instead of doing loose substring counting
- surfaces operational metrics that resemble real observability and traffic-analysis tasks
- includes both human-readable and JSON output modes for scripting
- handles malformed lines, missing byte counts, and optional latency fields safely

## Stack
- Python 3
- standard library only

## Features
- parses common log lines like `IP - - [time] "METHOD /path HTTP/1.1" 200 123`
- also parses combined log tails with referrer and user-agent fields
- optionally parses a trailing response-time token and normalizes it to milliseconds
- counts requests by HTTP status code and request method
- reports top client IPs, paths, referrers, and user agents
- tracks total bytes, average bytes per request, malformed line count, and latency percentiles when present
- supports `--top` and `--format text|json`

## Usage
```bash
python3 log_analyzer.py access.log
python3 log_analyzer.py access.log --top 5
python3 log_analyzer.py access.log --format json
```

The parser accepts:
- common logs: `IP - - [time] "METHOD /path HTTP/1.1" 200 123`
- combined logs: `... 200 123 "https://referrer.example/" "Mozilla/5.0"`
- optional latency tails after either format:
  - decimal values are treated as seconds (for example `0.245` -> `245.0 ms`)
  - integer values are treated as microseconds (for example `12345` -> `12.345 ms`)

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
```

## Test
```bash
python3 -m unittest discover -s projects/log-analyzer -p "test_*.py"
```

## Future Improvements
- export CSV summaries for spreadsheet-friendly analysis
- add per-path latency breakdowns so slow endpoints stand out directly in the report
- add time-window or status-filter options for larger operational datasets

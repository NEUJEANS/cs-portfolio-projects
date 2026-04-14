# log-analyzer

## Overview
Analyze common web access logs from the command line with per-status, per-method, top-IP, and top-path summaries.

## Why it is portfolio-worthy
- parses structured log lines instead of doing loose substring counting
- surfaces operational metrics that resemble real observability tasks
- includes both human-readable and JSON output modes for scripting
- handles malformed lines and missing byte counts safely

## Stack
- Python 3
- standard library only

## Features
- parses common access log lines like `IP - - [time] "METHOD /path HTTP/1.1" 200 123`
- counts requests by HTTP status code and request method
- reports top client IPs and most requested paths
- tracks total bytes, average bytes per request, and malformed line count
- supports `--top` and `--format text|json`

## Usage
```bash
python3 log_analyzer.py access.log
python3 log_analyzer.py access.log --top 5
python3 log_analyzer.py access.log --format json
```

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
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- add support for combined logs with referrer/user-agent capture
- include latency percentiles when upstream logs provide response time fields
- export CSV summaries for spreadsheet-friendly analysis

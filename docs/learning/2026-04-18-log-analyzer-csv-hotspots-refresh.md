# Learning refresh — 2026-04-18 — log-analyzer CSV + hotspot slice

## Python/tool refresh
- `csv.DictWriter` is the simplest standard-library way to emit stable column-oriented exports for spreadsheet tools.
- When writing CSV files from Python, open the destination with `newline=""` to avoid platform-specific blank-line issues.
- A mixed report can stay user-friendly on stdout (`text` / `json`) while optional `--summary-csv` and `--path-latency-csv` side-effect files support downstream charting.

## Self-test plan
- emit one summary CSV with scalar metrics plus ranked counters
- emit one path-latency CSV with one row per hotspot path
- confirm CLI still prints normal text/JSON output while writing those files

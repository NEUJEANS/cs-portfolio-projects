# log-analyzer

## Overview
Analyze common, combined, and latency-augmented web access logs from the command line with time-window slicing, minute/hour trend bucketing, per-status, per-method, top-IP, top-path, referrer, user-agent, request-latency, upstream-latency, deployment/environment facet breakdowns, side-by-side release/deployment comparisons, and incident-style per-path hotspot drill-downs.

## Why it is portfolio-worthy
- parses realistic common and combined access-log lines instead of doing loose substring counting
- surfaces operational metrics that resemble real observability and traffic-analysis tasks
- includes both human-readable and machine-friendly outputs for scripting, spreadsheets, and chart pipelines
- highlights slow endpoints directly with per-path request and upstream latency hotspot summaries
- supports status/method-filtered hotspot drill-downs plus bounded time-window analysis for incident-response style investigations
- exports minute/hour trend buckets so students can turn raw logs into screenshot-ready latency and error-rate stories
- renders standalone SVG and HTML mini trend cards directly from active time buckets so GitHub Pages / slides can show release or incident snapshots without spreadsheet cleanup
- splits hotspot and trend views by named deployment/environment fields such as `env=prod`, `region=us-east-1`, or `release=2026.04` when richer log formats include them
- compares two facet values side by side (for example `prod` vs `staging`) with request/error/latency deltas plus aligned time-bucket rows for release reviews
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
- supports standalone `--time-bucket-card-svg` and `--time-bucket-card-html` exports for presentation-ready mini trend cards, browser-friendly artifact pages, optional timeline annotations with note/deploy/rollback/incident/recovery themes, and built-in preset stories for common deploy/incident/recovery narratives
- supports repeatable `--facet-field` selections so richer named log fields can drive per-facet hotspot and trend breakdowns in text, JSON, and dedicated CSV exports
- supports `--facet-compare-field`, `--facet-compare-values`, and `--facet-compare-csv` so two named-field values can be diffed side by side for release-review write-ups and spreadsheet exports
- supports standalone `--facet-compare-card-svg` and `--facet-compare-card-html` exports for release-review screenshots, browser-friendly comparison pages, and optional deploy/incident callouts
- supports `--top`, `--latency-paths`, `--summary-csv`, `--path-latency-csv`, `--path-latency-facet-csv`, `--upstream-path-latency-csv`, `--upstream-path-latency-facet-csv`, `--time-bucket`, `--time-bucket-csv`, `--time-bucket-facet-csv`, `--time-bucket-card-svg`, `--time-bucket-card-html`, `--card-annotation`, `--card-annotation-preset`, `--facet-field`, `--facet-compare-field`, `--facet-compare-values`, `--facet-compare-csv`, `--facet-compare-card-svg`, `--facet-compare-card-html`, `--hotspot-status`, `--hotspot-method`, `--window-start`, `--window-end`, and `--format text|json`

## Usage
```bash
python3 log_analyzer.py access.log
python3 log_analyzer.py access.log --top 5
python3 log_analyzer.py access.log --format json
python3 log_analyzer.py access.log --summary-csv summary.csv --path-latency-csv hotspots.csv
python3 log_analyzer.py access.log --path-latency-csv request-hotspots.csv --upstream-path-latency-csv upstream-hotspots.csv
python3 log_analyzer.py access.log --time-bucket minute --format json
python3 log_analyzer.py access.log --time-bucket minute --time-bucket-csv minute-trends.csv --summary-csv summary.csv
python3 log_analyzer.py access.log --time-bucket minute --time-bucket-card-svg trend-card.svg --time-bucket-card-html trend-card.html
python3 log_analyzer.py access.log --time-bucket minute --time-bucket-card-svg trend-card.svg --card-annotation '2026-04-18T09:00:20Z=deploy|Deploy started' --card-annotation '2026-04-18T09:01:40Z=rollback|Rollback triggered'
python3 log_analyzer.py access.log --time-bucket minute --time-bucket-card-svg trend-card.svg --time-bucket-card-html trend-card.html --card-annotation-preset 'deploy-incident-recovery=2026-04-18T09:00:20Z,2026-04-18T09:01:40Z,2026-04-18T09:03:10Z'
python3 log_analyzer.py access.log --hotspot-status 500 --hotspot-status 502 --hotspot-method POST --format json
python3 log_analyzer.py access.log --window-start 2026-04-18T09:00:00Z --window-end 2026-04-18T10:00:00Z --time-bucket hour --format json
python3 log_analyzer.py access.log --facet-field env --facet-field region --time-bucket minute --time-bucket-facet-csv bucket-facets.csv --path-latency-facet-csv hotspot-facets.csv
python3 log_analyzer.py access.log --time-bucket minute --facet-compare-field env --facet-compare-values prod staging --facet-compare-csv release-compare.csv
python3 log_analyzer.py access.log --time-bucket minute --facet-compare-field env --facet-compare-values prod staging --facet-compare-card-svg release-compare-card.svg --facet-compare-card-html release-compare-card.html
python3 log_analyzer.py access.log --time-bucket minute --facet-compare-field env --facet-compare-values prod staging --facet-compare-card-svg release-compare-card.svg --card-annotation '2026-04-18T09:00:20Z=deploy|Deploy started' --card-annotation '2026-04-18T09:01:40Z=rollback|Rollback triggered'
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
- additional named `key=value` fields such as `env=prod`, `region=us-east-1`, or `release=2026.04` are preserved and can be surfaced with repeatable `--facet-field` flags

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
Use `--time-bucket minute` or `--time-bucket hour` when you want the matched requests summarized into chart-friendly trend buckets after any active `--window-start` / `--window-end` filtering is applied. Add one or more `--facet-field` values when you also want per-environment/per-region bucket breakdowns from richer `key=value` log tails.

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
- `--time-bucket minute --facet-field env --facet-field region --time-bucket-facet-csv bucket-facets.csv` exports one row per bucket/facet combination so deploy, shard, or region charts can be split without extra spreadsheet wrangling

## Facet comparisons for release reviews
Use `--facet-compare-field FIELD --facet-compare-values LEFT RIGHT` when you want two deployment, release, or environment values compared side by side without losing the normal global summary. This is useful for portfolio screenshots and release-review notes such as `env=prod` vs `env=staging` or `release=2026.04` vs `release=2026.05`.

Behavior:
- text output adds a compact comparison section with per-side request/error/latency summaries plus deltas
- JSON output includes a `facet_comparison` object with per-side summaries and an aligned `time_buckets` array when `--time-bucket` is active
- `--facet-compare-csv` writes one summary row plus one row per aligned bucket, making it easy to drop the comparison into Sheets or a notebook
- `--summary-csv` also records the active comparison field/values so downstream exports stay self-describing
- missing buckets are padded with zero-request rows so `prod` and `staging` stay aligned minute by minute or hour by hour

Examples:
- `--facet-compare-field env --facet-compare-values prod staging`
- `--time-bucket minute --facet-compare-field env --facet-compare-values prod staging --facet-compare-csv release-compare.csv`
- combine with `--window-start` / `--window-end` to isolate the deploy window before comparing the two slices

## Comparison card artifacts
Use `--facet-compare-card-svg` when you want one standalone visual comparison card for slides, README screenshots, or release-review thumbnails. Use `--facet-compare-card-html` when you also want a browser-friendly artifact page with the same inline SVG plus exact summary and aligned per-bucket delta tables.

Behavior:
- both flags require `--facet-compare-field` and `--facet-compare-values`
- they reuse the existing comparison summary and aligned time-bucket rows instead of creating a separate analysis path
- the SVG card highlights request/error/latency deltas plus three side-by-side bucket charts (requests, error rate, average latency)
- the HTML companion repeats the card and adds exact summary + per-bucket tables for verification, captions, and copy/paste into docs
- add repeatable `--card-annotation TIMESTAMP=LABEL` or `TIMESTAMP=THEME|LABEL` flags (with `--time-bucket`) to pin numbered deploy/incident markers onto shared bucket rows in both the SVG footer and HTML annotation/table views
- use `--card-annotation-preset PRESET=TIMESTAMP[,TIMESTAMP...]` when you want built-in stories such as `deploy-incident-recovery` or `deploy-rollback-recovery` without repeating three separate annotation labels/themes on the CLI
- explicit themes currently include `note`, `deploy`, `rollback`, `incident`, and `recovery`, each with distinct marker colors and badges in SVG/HTML exports
- when `--time-bucket` is omitted, the card still renders a summary-only comparison and the HTML table explains that no aligned bucket rows were produced

Examples:
- `--facet-compare-field env --facet-compare-values prod staging --facet-compare-card-svg release-compare-card.svg`
- `--time-bucket minute --facet-compare-field env --facet-compare-values prod staging --facet-compare-card-svg release-compare-card.svg --facet-compare-card-html release-compare-card.html`
- `--time-bucket minute --facet-compare-field env --facet-compare-values prod staging --facet-compare-card-svg release-compare-card.svg --card-annotation '2026-04-18T09:00:20Z=deploy|Deploy started' --card-annotation '2026-04-18T09:01:40Z=rollback|Rollback triggered'`
- `--time-bucket minute --facet-compare-field env --facet-compare-values prod staging --facet-compare-card-svg release-compare-card.svg --card-annotation-preset 'deploy-rollback-recovery=2026-04-18T09:00:20Z,2026-04-18T09:01:40Z,2026-04-18T09:03:10Z'`
- sample committed artifacts live under `docs/artifacts/log-analyzer/`, including annotated trend/comparison card bundles

## Trend card artifacts
Use `--time-bucket-card-svg` when you want one standalone visual card for slides, README screenshots, or portfolio thumbnails. Use `--time-bucket-card-html` when you also want a browser-friendly artifact page with the same inline SVG plus a bucket summary table.

Behavior:
- both flags require `--time-bucket`
- the SVG card highlights matched requests, overall error rate, weighted average latency, and the busiest / noisiest / slowest buckets
- the HTML companion repeats the card and adds a tabular per-bucket breakdown with explicit bucket start/end boundaries for copy/paste-friendly captions or verification
- add repeatable `--card-annotation TIMESTAMP=LABEL` or `TIMESTAMP=THEME|LABEL` flags to pin numbered deploy/incident markers onto matching buckets in both the SVG footer and HTML legend/table
- use `--card-annotation-preset PRESET=TIMESTAMP[,TIMESTAMP...]` to expand common three-step stories such as `deploy-incident-recovery` without retyping the built-in labels/themes every run
- explicit themes currently include `note`, `deploy`, `rollback`, `incident`, and `recovery`; unknown theme names fail fast so screenshots do not silently lose severity cues
- when `--facet-field` is active, the HTML page also surfaces the selected facet names plus how many facet trend rows were exported alongside the card

Examples:
- `--time-bucket minute --time-bucket-card-svg release-trend.svg`
- `--time-bucket minute --time-bucket-card-svg release-trend.svg --time-bucket-card-html release-trend.html`
- `--time-bucket minute --time-bucket-card-svg release-trend.svg --card-annotation '2026-04-18T09:00:20Z=deploy|Deploy started' --card-annotation '2026-04-18T09:01:40Z=incident|Error budget burn'`
- `--time-bucket minute --time-bucket-card-svg release-trend.svg --time-bucket-card-html release-trend.html --card-annotation-preset 'deploy-incident-recovery=2026-04-18T09:00:20Z,2026-04-18T09:01:40Z,2026-04-18T09:03:10Z'`
- combine with `--summary-csv`, `--time-bucket-csv`, and `--time-bucket-facet-csv` when you want both the visual card and spreadsheet/debugging companions in one run

## Hotspot drill-downs
Use `--hotspot-status` and `--hotspot-method` when you want the per-path hotspot sections and CSV exports to focus on a particular incident slice while keeping the top-level totals and percentile summaries global **within the currently selected time window**. Add `--facet-field` when those hotspot rows should also be split by deploy/release/region metadata already present in the log line.

Examples:
- `--hotspot-status 500 --hotspot-status 502` isolates failing paths in the hotspot tables/exports
- `--hotspot-method POST` focuses the hotspot tables/exports on mutating requests
- combine both flags to highlight slow failing write endpoints without losing the overall traffic summary for the selected time window

When filters are active:
- text output annotates the hotspot section headings with the active filters
- JSON output includes a `hotspot_filters` object
- hotspot CSV exports add `status_filter` and `method_filter` columns so downstream charts stay self-describing
- facet-aware hotspot CSV exports add `facet_label` plus one `facet_<field>` column per selected `--facet-field`

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

Use `--path-latency-facet-csv` and `--upstream-path-latency-facet-csv` together with one or more `--facet-field` selections to export the same hotspot schema plus:
- `facet_label`
- one `facet_<field>` column per selected field (for example `facet_env`, `facet_region`)

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

Use `--time-bucket-facet-csv` with both `--time-bucket` and `--facet-field` to export the same trend schema plus `facet_label` and one `facet_<field>` column per selected field.

Use `--facet-compare-csv` with `--facet-compare-field` and `--facet-compare-values` to export:
- one `summary` row with left/right request, error-rate, latency, upstream-latency, and top-path metrics
- one `bucket` row per aligned minute/hour bucket when `--time-bucket` is active
- delta columns such as `request_count_delta`, `p95_latency_ms_delta`, and `max_upstream_latency_ms_delta`

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
Time bucket facet breakdowns: (facets: env, region)
  2026-04-18T09:00:00+00:00 | env=prod, region=us-east-1 -> requests=30, errors=6 (20.0%), top_path=/api/export (6)
    request latency: samples=29, avg=22.4, p95=58.0, max=109.0
    upstream latency: samples=21, avg=16.2, p95=40.1, max=51.0
Facet comparison (env): prod vs staging (delta: staging minus prod)
  env=prod -> requests=30, errors=6 (20.0%), avg_latency=22.4 ms, p95_latency=58.0 ms, avg_upstream=16.2 ms, p95_upstream=40.1 ms, top_path=/api/export (6)
  env=staging -> requests=12, errors=1 (8.333%), avg_latency=11.8 ms, p95_latency=24.5 ms, avg_upstream=7.4 ms, p95_upstream=15.2 ms, top_path=/api/export (3)
  delta -> requests=-18, errors=-5, error_rate=-11.667 pp, avg_latency=-10.6 ms, p95_latency=-33.5 ms, avg_upstream=-8.8 ms, p95_upstream=-24.9 ms
Facet comparison buckets (hour):
  2026-04-18T09:00:00+00:00 -> prod: requests=30, error_rate=20.0%, avg_latency=22.4 ms | staging: requests=12, error_rate=8.333%, avg_latency=11.8 ms | delta requests=-18, error_rate=-11.667 pp, avg_latency=-10.6 ms
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
Per-path latency hotspots by facet (ms): (filters: status=500,502; method=POST) (facets: env, region)
  /api/export | env=prod, region=us-east-1: count=4, avg=94.8, p95=120.0, max=121.0
Per-path upstream latency hotspots (ms): (filters: status=500,502; method=POST)
  /api/export: count=5, avg=73.6, p95=99.0, max=101.4
Per-path upstream latency hotspots by facet (ms): (filters: status=500,502; method=POST) (facets: env, region)
  /api/export | env=prod, region=us-east-1: count=4, avg=79.1, p95=100.2, max=101.4
```

## Test
```bash
python3 -m unittest discover -s projects/log-analyzer -p "test_*.py"
```

## Future Improvements
- optionally support facet-aware ranking summaries for top IP/path tables when richer custom log formats include deployment labels
- consider PNG export helpers or a small gallery index page that links trend cards and comparison cards together
- add a small preset/legend helper so repeated deploy-incident-recovery stories can be exported with less CLI repetition

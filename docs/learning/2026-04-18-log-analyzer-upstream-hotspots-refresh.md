# Learning refresh — 2026-04-18 — log-analyzer upstream hotspot slice

## Python/tool refresh
- The existing `summarize_path_latencies(...)` helper can be reused for upstream hotspots, so this slice can stay surgical instead of adding a second summary implementation.
- `upstream_response_time=` values should only contribute to the upstream-path view when they are actually present; paths without upstream timing data should stay out of the upstream hotspot report.
- Reusing the same CSV schema for request-path and upstream-path exports keeps downstream charting simple.

## Self-test plan
- confirm `analyze_lines(...)` returns a separate `upstream_path_latency_breakdown`
- confirm the upstream path breakdown sorts by average latency and respects the existing path-limit control
- confirm text output adds a distinct upstream hotspot section
- confirm JSON output exposes the new breakdown and CSV export writes the expected rows
- confirm the existing request-latency breakdown behavior remains unchanged
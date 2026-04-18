# Learning refresh — 2026-04-18 — log-analyzer Nginx timing fields slice

## Python/tool refresh
- A single regex can keep parsing the stable common/combined prefix while a second small parser handles optional trailing `key=value` timing tokens.
- Nginx named timing fields are always documented in seconds with millisecond resolution, so they should not reuse the older unnamed integer-latency heuristic that treated bare integers as microseconds.
- Multi-attempt upstream timing values can be aggregated safely by splitting on commas/colons, trimming whitespace, and ignoring `-` placeholders.

## Self-test plan
- confirm old unnamed latency lines still parse exactly as before
- confirm `request_time=` drives the primary latency summary
- confirm `upstream_response_time=` produces a separate upstream summary and survives retry-style multi-value fields
- confirm CSV/text/JSON outputs all surface the new summary without breaking existing report sections

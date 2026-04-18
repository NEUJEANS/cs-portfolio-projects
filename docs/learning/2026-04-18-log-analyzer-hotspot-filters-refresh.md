# Learning refresh — 2026-04-18 — log-analyzer hotspot filters slice

## Python/tool refresh
- `analyze_lines(...)` is already the clean choke point for deciding which parsed entries feed each summary bucket, so hotspot filtering can stay surgical.
- The same parsed line can contribute to the global latency summaries even when it is intentionally excluded from the hotspot drill-downs.
- Reusing the existing path-latency summarizer keeps the feature small; the main new work is filter normalization, CLI wiring, and output metadata.

## Self-test plan
- confirm filtered hotspot breakdowns include only matching status/method entries
- confirm the global request and upstream latency summaries remain unchanged by hotspot filters
- confirm text output labels the filtered hotspot sections clearly
- confirm JSON output exposes the active filters
- confirm hotspot CSV exports keep the filtered rows self-describing via metadata columns
- confirm invalid hotspot status values fail fast at the CLI boundary

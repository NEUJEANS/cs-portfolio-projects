# Self-test note — robin-hood-hashing-lab lookup percentile slice

Date: 2026-04-21

## Refresh
- Refreshed the pooled-percentile math by mirroring the repo's existing percentile helper style instead of inventing a new ranking rule.
- Rechecked that weighted histogram summaries are the right abstraction here because every benchmark report is already aggregated across deterministic trials.

## Quick self-test
- Built a synthetic `BenchmarkRow` pair in the unit suite where successful and unsuccessful lookup histograms differ across trials.
- Verified the pooled summary now reports the expected successful-lookup `avg / p50 / p95 / max` values instead of only means.
- Verified CSV export preserves numeric ordering for the new `successful_lookup_probe_histogram` keys the same way it already did for the other histograms.

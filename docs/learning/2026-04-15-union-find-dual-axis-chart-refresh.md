# Union-Find dual-axis chart refresh + self-test

## Refresh notes
- Benchmark-series payloads already contain `edges_requested`, `edges_per_second`, and `stats.largest_component`.
- A dual-axis SVG is a good fit when the two metrics have different scales but share the same x-axis.
- CSV re-rendering must work too, so the chart builder should read both JSON benchmark artifacts and benchmark CSV exports.

## Self-test checklist
- Confirm benchmark JSON has `stats.largest_component` for every run.
- Confirm benchmark CSV export preserves `stats_largest_component`.
- Confirm SVG labels clearly distinguish throughput from largest-component size.
- Confirm the chart remains deterministic when re-rendered from the committed sample artifact.

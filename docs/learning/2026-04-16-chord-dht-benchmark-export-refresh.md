# Chord DHT benchmark export refresh

Timestamp: 2026-04-16 02:03 UTC

## Quick refresh
- Reuse the benchmark payload as the single source of truth so summary math and exported rows cannot drift.
- Markdown export should optimize for readability: a short summary plus one table with hop counts and routes.
- CSV export should optimize for downstream processing: one machine-readable row per benchmark case.

## Self-test
- If start nodes are filtered on the CLI, does the export preserve that subset? Yes — it passes `args.start_nodes` directly into `benchmark_lookups(...)`.
- Should routes in CSV use the Markdown arrow glyph? No — use a plain ASCII separator (`->`) so spreadsheets/scripts stay safe.
- What should stay out of scope for this slice? New benchmark algorithms or statistical variance sampling; this slice is about exporting the current benchmark cleanly.

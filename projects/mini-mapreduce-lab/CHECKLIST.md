# mini-mapreduce-lab checklist

## Completed slices
- [x] Implement local MapReduce execution with shard-level combine, reducer partitioning, and JSON output
- [x] Add built-in `wordcount` and `json-group-count` jobs plus reproducible benchmark mode
- [x] Support external Python plugins for custom mapper/reducer/combiner logic
- [x] Add plugin-defined benchmark generators and dataset-family metadata
- [x] Add plugin inspection, diff, catalog, and dedicated plugin-doc page generation
- [x] Export benchmark artifacts as CSV, heatmap CSV, Markdown, and standalone HTML with inline SVG charts
- [x] Surface structured benchmark annotations with severity, hotspot keys, and takeaways in JSON/Markdown/HTML artifacts
- [x] Add annotation filtering, card limits, and overflow-summary callouts for tighter benchmark reports
- [x] Add batch benchmark presets that export both full and filtered annotation views in one run
- [x] Add a compact docs index page that links benchmark artifacts, plugin docs, and inspection diffs together
- [x] Add a richer observability-style plugin example with service-latency summaries and incident/batch benchmark families
- [x] Add a sessionization analytics plugin example with product-usage benchmark families and reviewer-friendly session summaries
- [x] Add a streaming-window telemetry plugin example with deterministic five-minute buckets, IoT/live-ops benchmark families, and publishable docs artifacts
- [x] Add a watermark-aware late-event summary plugin example with deterministic replay/backfill families, late/drop metrics, and publishable docs artifacts
- [x] Add a rolling-window joins plugin example so the lab can compare multi-stream correlation against the existing score/latency/sessionization/windowing/out-of-order stories

## Next candidate slices
- [ ] Add repository-level inspection summaries or release-to-release comparison pages that compare multiple plugin snapshots across releases
- [ ] Add docs-site navigation sidebars or cross-project landing pages if the artifact surface keeps growing

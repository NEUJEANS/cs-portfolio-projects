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

## Next candidate slices
- [ ] Add richer plugin examples beyond score aggregation, such as sessionization or log-latency summaries
- [ ] Add repository-level inspection summaries or release-to-release comparison pages that compare multiple plugin snapshots across releases
- [ ] Add docs-site navigation sidebars or cross-project landing pages if the artifact surface keeps growing

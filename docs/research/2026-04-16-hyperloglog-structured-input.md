# HyperLogLog structured-input research

## Goal
Add a meaningful follow-up slice to `hyperloglog-cardinality-lab` so the project can count distinct IDs directly from realistic CSV exports and JSON event logs instead of requiring pre-flattened newline text files.

## Brief findings
- HyperLogLog stays most convincing in analytics/distributed-systems portfolio stories when it plugs into real event streams such as user IDs, visitor IDs, or SKU fields rather than synthetic plain-text inputs.
- Production writeups consistently emphasize mergeable shard-local sketches plus straightforward field extraction from structured logs before sketching.
- JSON Lines is a practical default for event streams because each line is independently parseable and easy to resume.
- CSV ingestion should assume header-based field selection first because exported analytics/reporting files usually already carry stable column names.
- Dotted JSON field paths are enough for a strong local portfolio slice; they demonstrate nested-event extraction without pulling in a heavy JSONPath dependency.

## Applied product decisions
- extend `build` instead of inventing a second ingestion command
- support `.csv`, `.jsonl`/`.ndjson`, and `.json` via extension-based auto detection
- support `--field` for CSV columns and dotted JSON paths
- keep extraction scalar-only so the counted entity stays explicit and interview-friendly

## References
- Google Analytics developer write-up on HyperLogLog++ and approximate distinct counting
- Facebook engineering overview of HyperLogLog use in data infrastructure
- general HyperLogLog references covering mergeability, small-range correction, and analytics use cases

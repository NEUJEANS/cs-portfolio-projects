# Mini MapReduce JSON benchmark self-test

Date: 2026-04-16 08:22 UTC
Project: `mini-mapreduce-lab`

## Refresh
- `json.dumps(..., sort_keys=True)` keeps synthetic JSONL fixtures deterministic for test snapshots and artifact diffs.
- The existing `map_json_group_count()` path already handles missing/null grouping values, so the benchmark slice should reuse that path instead of inventing a benchmark-only reducer.
- For benchmark parity, the synthetic runner should pass the selected `group_field` through `execute_job()` as well as the shard-local mapper used for heatmap summaries.

## Quick self-check
- If `benchmark --job json-group-count --group-field status` runs through `execute_job()`, reducer stats and heatmap summaries stay aligned.
- If `dataset_family` validation lives in `build_benchmark_lines()`, CLI and programmatic calls fail consistently.

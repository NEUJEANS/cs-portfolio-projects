# mini-mapreduce heatmap refresh

Date: 2026-04-15

## Quick refresh
- `csv.DictWriter` keeps benchmark export headers deterministic when the field order is fixed up front.
- A shard-to-reducer heatmap can be represented as tidy rows instead of nested matrices, which makes it easier to chart in spreadsheets or notebooks.
- For this lab, per-cell `records` should reflect the combiner-compressed count routed from one shard into one reducer bucket; `unique_keys` explains whether skew comes from hot keys or from many distinct keys.

## Self-test
- With 120 synthetic records and `--shard-size 20`, the benchmark should produce 6 shards.
- With `--reducers 2`, heatmap CSV should therefore emit `6 * 2 = 12` data rows plus the header.
- The header contract for the new export is:
  `scenario,seed,reducers,shard_index,reducer,records,unique_keys`

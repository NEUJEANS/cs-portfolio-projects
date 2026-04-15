# mini-mapreduce plugin review pass 1

## Focus
Plugin execution correctness.

## Findings
1. The first plugin design reused the built-in shard combiner, which summed values before the custom reducer ran. That broke max-style plugin reducers (`Alice,4` + `Alice,9` became `13` instead of `9`).

## Fixes applied
- Generalized the combiner step so plugins can provide `combine_values(key, values)`.
- Updated the example max-score plugin to use `max` for both combine and reduce.
- Re-ran project and repo tests after the pipeline change.

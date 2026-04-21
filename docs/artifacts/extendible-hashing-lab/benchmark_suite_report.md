# Extendible hashing vs linear probing, cuckoo hashing, and B-tree benchmark comparison

- Suite source: `projects/extendible-hashing-lab/benchmark_suite.json`
- Scenario count: `4`
- Extendible bucket capacity: `2`
- Linear probing capacity / max load / tombstone ratio: `8` / `0.75` / `0.25`
- Cuckoo starting capacity: `7`
- Cuckoo max displacements: `8`
- B-tree minimum degree: `2`
- B-tree page size / value bytes: `512` / `32`
- Trials per scenario: `3`

## Linear probing theory overlay
- Formula: `successful ≈ 0.5 * (1 + 1 / (1 - α)); unsuccessful ≈ 0.5 * (1 + 1 / (1 - α)^2)`
- Reference basis: Use the average occupied load factor α across benchmark steps as the compact baseline; final and peak occupied load factors are included for context.

| Scenario | Avg occupied α | Peak occupied α | Expected hit @ avg α | Observed hit | Δ | Expected miss @ avg α | Observed miss | Δ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| directory-friendly-read-heavy | 0.5481 | 0.75 | 1.606 | 1.333 | -0.273 | 2.948 | 2.5 | -0.448 |
| split-pressure-growth | 0.5134 | 0.75 | 1.528 | 1.0 | -0.528 | 2.612 | 2.0 | -0.612 |
| delete-heavy-churn | 0.5536 | 0.875 | 1.62 | 1.0 | -0.62 | 3.009 | 4.0 | 0.991 |
| primary-clustering-tombstone-pressure | 0.4779 | 0.625 | 1.458 | 3.333 | 1.875 | 2.334 | 5.0 | 2.666 |

## Scenario scoreboard
| Scenario | Ops | Final entries | Ext splits | Ext merges | Peak depth | Linear avg probes | Linear get hit/miss avg | Linear max probe | Cuckoo avg rehashes | Cuckoo avg displacements | B-tree height | B-tree nodes | B-tree paged bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| directory-friendly-read-heavy | 13 | 5 | 3 | 0 | 3 | 1.462 | 1.333 / 2.5 | 3 | 0.333 | 4.0 | 2 | 3 | 1569 |
| split-pressure-growth | 14 | 10 | 5 | 0 | 3 | 1.357 | 1.0 / 2.0 | 2 | 1.0 | 11.333 | 2 | 4 | 2081 |
| delete-heavy-churn | 14 | 5 | 4 | 1 | 3 | 1.357 | 1.0 / 4.0 | 4 | 0.0 | 2.333 | 2 | 3 | 1569 |
| primary-clustering-tombstone-pressure | 17 | 3 | 7 | 4 | 3 | 3.471 | 3.333 / 5.0 | 6 | 0.0 | 1.333 | 1 | 1 | 545 |

## Scenario — directory-friendly-read-heavy

- Description: Warm up a small user cache, then mostly read/update the stable working set with a few misses and one delete.
- Operation mix: `puts=7` (`insertions=6`, `updates=1`), `gets=5` (`hits=3`, `misses=2`), `deletes=1` (`hits=1`, `misses=0`)
- Extendible hashing finished at global depth `3` with `4` buckets and load factor `0.625` after `3` splits / `0` merges and `3` directory growth(s) / `0` directory shrink(s).
- Linear probing baseline finished at capacity `8` with load factor `0.625`, tombstones `1`, average probe count `1.462`, max probe `3`, and `0` rebuild(s).
- Linear lookup probe split: successful gets avg/p50/p95/max = `1.333 / 1 / 2 / 2`; unsuccessful gets avg/p50/p95/max = `2.5 / 2 / 3 / 3`.
- Linear theory overlay: Average occupied α≈0.5481 predicts about 1.606 successful probes and 2.948 unsuccessful probes; observed hit/miss averages were 1.333 and 2.5. Peak occupied α≈0.75 gives miss-cost context for the clustering spikes.
- Linear phase probe split: puts avg/p50/p95/max = `1.286 / 1 / 2 / 2`; gets avg/p50/p95/max = `1.8 / 2 / 3 / 3`; deletes avg/p50/p95/max = `1.0 / 1 / 1 / 1`.
- Cuckoo hashing averaged `0.333` rehashes and `4.0` displacements, finishing between capacities `7` and `15`.
- B-tree page baseline finished at height `2` across `3` node(s); at `page_size=512` and `value_bytes=32` the paged snapshot would occupy `1569` bytes with `359` bytes of fixed slack per page.
- Validation: final states matched across `3` deterministic trial(s).

| Linear phase | Count | Avg probes | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| puts | 7 | 1.286 | 1 | 2 | 2 |
| gets | 5 | 1.8 | 2 | 3 | 3 |
| deletes | 1 | 1.0 | 1 | 1 | 1 |

| Trial | Extendible splits | Extendible merges | Peak depth | Peak buckets | Peak directory slots | Linear avg probes | Linear get hit avg | Linear get miss avg | Linear get miss p95 | Linear max probe | Linear rebuilds | Cuckoo rehashes | Cuckoo displacements | Cuckoo final capacity | B-tree height | B-tree nodes | B-tree paged bytes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 3 | 0 | 3 | 4 | 8 | 1.462 | 1.333 | 2.5 | 3 | 3 | 0 | 1 | 12 | 15 | 2 | 3 | 1569 |
| 2 | 3 | 0 | 3 | 4 | 8 | 1.462 | 1.333 | 2.5 | 3 | 3 | 0 | 0 | 0 | 7 | 2 | 3 | 1569 |
| 3 | 3 | 0 | 3 | 4 | 8 | 1.462 | 1.333 | 2.5 | 3 | 3 | 0 | 0 | 0 | 7 | 2 | 3 | 1569 |

## Scenario — split-pressure-growth

- Description: Force repeated low-bit collisions so extendible hashing must split buckets while cuckoo hashing spends work on displacement and occasional rehashing.
- Operation mix: `puts=11` (`insertions=10`, `updates=1`), `gets=3` (`hits=2`, `misses=1`), `deletes=0` (`hits=0`, `misses=0`)
- Extendible hashing finished at global depth `3` with `6` buckets and load factor `0.8333` after `5` splits / `0` merges and `3` directory growth(s) / `0` directory shrink(s).
- Linear probing baseline finished at capacity `16` with load factor `0.625`, tombstones `0`, average probe count `1.357`, max probe `2`, and `1` rebuild(s).
- Linear lookup probe split: successful gets avg/p50/p95/max = `1.0 / 1 / 1 / 1`; unsuccessful gets avg/p50/p95/max = `2.0 / 2 / 2 / 2`.
- Linear theory overlay: Average occupied α≈0.5134 predicts about 1.528 successful probes and 2.612 unsuccessful probes; observed hit/miss averages were 1 and 2. Peak occupied α≈0.75 gives miss-cost context for the clustering spikes.
- Linear phase probe split: puts avg/p50/p95/max = `1.364 / 1 / 2 / 2`; gets avg/p50/p95/max = `1.333 / 1 / 2 / 2`; deletes avg/p50/p95/max = `0.0 / 0 / 0 / 0`.
- Cuckoo hashing averaged `1.0` rehashes and `11.333` displacements, finishing between capacities `15` and `15`.
- B-tree page baseline finished at height `2` across `4` node(s); at `page_size=512` and `value_bytes=32` the paged snapshot would occupy `2081` bytes with `359` bytes of fixed slack per page.
- Validation: final states matched across `3` deterministic trial(s).

| Linear phase | Count | Avg probes | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| puts | 11 | 1.364 | 1 | 2 | 2 |
| gets | 3 | 1.333 | 1 | 2 | 2 |
| deletes | 0 | 0.0 | 0 | 0 | 0 |

| Trial | Extendible splits | Extendible merges | Peak depth | Peak buckets | Peak directory slots | Linear avg probes | Linear get hit avg | Linear get miss avg | Linear get miss p95 | Linear max probe | Linear rebuilds | Cuckoo rehashes | Cuckoo displacements | Cuckoo final capacity | B-tree height | B-tree nodes | B-tree paged bytes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 5 | 0 | 3 | 6 | 8 | 1.357 | 1.0 | 2.0 | 2 | 2 | 1 | 1 | 14 | 15 | 2 | 4 | 2081 |
| 2 | 5 | 0 | 3 | 6 | 8 | 1.357 | 1.0 | 2.0 | 2 | 2 | 1 | 1 | 12 | 15 | 2 | 4 | 2081 |
| 3 | 5 | 0 | 3 | 6 | 8 | 1.357 | 1.0 | 2.0 | 2 | 2 | 1 | 1 | 8 | 15 | 2 | 4 | 2081 |

## Scenario — delete-heavy-churn

- Description: Grow a clustered directory, delete enough keys to trigger extendible merges and shrinks, then repopulate a smaller live set.
- Operation mix: `puts=8` (`insertions=8`, `updates=0`), `gets=2` (`hits=1`, `misses=1`), `deletes=4` (`hits=3`, `misses=1`)
- Extendible hashing finished at global depth `3` with `4` buckets and load factor `0.625` after `4` splits / `1` merges and `4` directory growth(s) / `1` directory shrink(s).
- Linear probing baseline finished at capacity `8` with load factor `0.625`, tombstones `0`, average probe count `1.357`, max probe `4`, and `1` rebuild(s).
- Linear lookup probe split: successful gets avg/p50/p95/max = `1.0 / 1 / 1 / 1`; unsuccessful gets avg/p50/p95/max = `4.0 / 4 / 4 / 4`.
- Linear theory overlay: Average occupied α≈0.5536 predicts about 1.62 successful probes and 3.009 unsuccessful probes; observed hit/miss averages were 1 and 4. Peak occupied α≈0.875 gives miss-cost context for the clustering spikes.
- Linear phase probe split: puts avg/p50/p95/max = `1.25 / 1 / 3 / 3`; gets avg/p50/p95/max = `2.5 / 1 / 4 / 4`; deletes avg/p50/p95/max = `1.0 / 1 / 1 / 1`.
- Cuckoo hashing averaged `0.0` rehashes and `2.333` displacements, finishing between capacities `7` and `7`.
- B-tree page baseline finished at height `2` across `3` node(s); at `page_size=512` and `value_bytes=32` the paged snapshot would occupy `1569` bytes with `359` bytes of fixed slack per page.
- Validation: final states matched across `3` deterministic trial(s).

| Linear phase | Count | Avg probes | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| puts | 8 | 1.25 | 1 | 3 | 3 |
| gets | 2 | 2.5 | 1 | 4 | 4 |
| deletes | 4 | 1.0 | 1 | 1 | 1 |

| Trial | Extendible splits | Extendible merges | Peak depth | Peak buckets | Peak directory slots | Linear avg probes | Linear get hit avg | Linear get miss avg | Linear get miss p95 | Linear max probe | Linear rebuilds | Cuckoo rehashes | Cuckoo displacements | Cuckoo final capacity | B-tree height | B-tree nodes | B-tree paged bytes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 4 | 1 | 3 | 4 | 8 | 1.357 | 1.0 | 4.0 | 4 | 4 | 1 | 0 | 4 | 7 | 2 | 3 | 1569 |
| 2 | 4 | 1 | 3 | 4 | 8 | 1.357 | 1.0 | 4.0 | 4 | 4 | 1 | 0 | 2 | 7 | 2 | 3 | 1569 |
| 3 | 4 | 1 | 3 | 4 | 8 | 1.357 | 1.0 | 4.0 | 4 | 4 | 1 | 0 | 1 | 7 | 2 | 3 | 1569 |

## Scenario — primary-clustering-tombstone-pressure

- Description: Force several keys into the same linear-probing slot, leave tombstones behind, then trigger a cleanup rebuild so the open-addressing clustering story is obvious in the exported metrics.
- Operation mix: `puts=7` (`insertions=7`, `updates=0`), `gets=6` (`hits=3`, `misses=3`), `deletes=4` (`hits=4`, `misses=0`)
- Extendible hashing finished at global depth `3` with `4` buckets and load factor `0.375` after `7` splits / `4` merges and `7` directory growth(s) / `4` directory shrink(s).
- Linear probing baseline finished at capacity `8` with load factor `0.375`, tombstones `0`, average probe count `3.471`, max probe `6`, and `1` rebuild(s).
- Linear lookup probe split: successful gets avg/p50/p95/max = `3.333 / 3 / 5 / 5`; unsuccessful gets avg/p50/p95/max = `5.0 / 6 / 6 / 6`.
- Linear theory overlay: Average occupied α≈0.4779 predicts about 1.458 successful probes and 2.334 unsuccessful probes; observed hit/miss averages were 3.333 and 5. Peak occupied α≈0.625 gives miss-cost context for the clustering spikes.
- Linear phase probe split: puts avg/p50/p95/max = `3.429 / 3 / 6 / 6`; gets avg/p50/p95/max = `4.167 / 3 / 6 / 6`; deletes avg/p50/p95/max = `2.5 / 2 / 4 / 4`.
- Cuckoo hashing averaged `0.0` rehashes and `1.333` displacements, finishing between capacities `7` and `7`.
- B-tree page baseline finished at height `1` across `1` node(s); at `page_size=512` and `value_bytes=32` the paged snapshot would occupy `545` bytes with `359` bytes of fixed slack per page.
- Validation: final states matched across `3` deterministic trial(s).

| Linear phase | Count | Avg probes | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| puts | 7 | 3.429 | 3 | 6 | 6 |
| gets | 6 | 4.167 | 3 | 6 | 6 |
| deletes | 4 | 2.5 | 2 | 4 | 4 |

| Trial | Extendible splits | Extendible merges | Peak depth | Peak buckets | Peak directory slots | Linear avg probes | Linear get hit avg | Linear get miss avg | Linear get miss p95 | Linear max probe | Linear rebuilds | Cuckoo rehashes | Cuckoo displacements | Cuckoo final capacity | B-tree height | B-tree nodes | B-tree paged bytes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 7 | 4 | 3 | 4 | 8 | 3.471 | 3.333 | 5.0 | 6 | 6 | 1 | 0 | 1 | 7 | 1 | 1 | 545 |
| 2 | 7 | 4 | 3 | 4 | 8 | 3.471 | 3.333 | 5.0 | 6 | 6 | 1 | 0 | 1 | 7 | 1 | 1 | 545 |
| 3 | 7 | 4 | 3 | 4 | 8 | 3.471 | 3.333 | 5.0 | 6 | 6 | 1 | 0 | 2 | 7 | 1 | 1 | 545 |


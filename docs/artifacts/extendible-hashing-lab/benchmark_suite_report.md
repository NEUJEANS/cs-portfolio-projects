# Extendible hashing vs cuckoo hashing and B-tree benchmark comparison

- Suite source: `projects/extendible-hashing-lab/benchmark_suite.json`
- Scenario count: `3`
- Extendible bucket capacity: `2`
- Cuckoo starting capacity: `7`
- Cuckoo max displacements: `8`
- B-tree minimum degree: `2`
- B-tree page size / value bytes: `512` / `32`
- Trials per scenario: `3`

## Scenario scoreboard
| Scenario | Ops | Final entries | Ext splits | Ext merges | Peak depth | Cuckoo avg rehashes | Cuckoo avg displacements | B-tree height | B-tree nodes | B-tree paged bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| directory-friendly-read-heavy | 13 | 5 | 3 | 0 | 3 | 0.333 | 4.0 | 2 | 3 | 1569 |
| split-pressure-growth | 14 | 10 | 5 | 0 | 3 | 1.0 | 11.333 | 2 | 4 | 2081 |
| delete-heavy-churn | 14 | 5 | 4 | 1 | 3 | 0.0 | 2.333 | 2 | 3 | 1569 |

## Scenario — directory-friendly-read-heavy

- Description: Warm up a small user cache, then mostly read/update the stable working set with a few misses and one delete.
- Operation mix: `puts=7` (`insertions=6`, `updates=1`), `gets=5` (`hits=3`, `misses=2`), `deletes=1` (`hits=1`, `misses=0`)
- Extendible hashing finished at global depth `3` with `4` buckets and load factor `0.625` after `3` splits / `0` merges and `3` directory growth(s) / `0` directory shrink(s).
- Cuckoo hashing averaged `0.333` rehashes and `4.0` displacements, finishing between capacities `7` and `15`.
- B-tree page baseline finished at height `2` across `3` node(s); at `page_size=512` and `value_bytes=32` the paged snapshot would occupy `1569` bytes with `359` bytes of fixed slack per page.
- Validation: final states matched across `3` deterministic trial(s).

| Trial | Extendible splits | Extendible merges | Peak depth | Peak buckets | Peak directory slots | Cuckoo rehashes | Cuckoo displacements | Cuckoo final capacity | B-tree height | B-tree nodes | B-tree paged bytes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 3 | 0 | 3 | 4 | 8 | 1 | 12 | 15 | 2 | 3 | 1569 |
| 2 | 3 | 0 | 3 | 4 | 8 | 0 | 0 | 7 | 2 | 3 | 1569 |
| 3 | 3 | 0 | 3 | 4 | 8 | 0 | 0 | 7 | 2 | 3 | 1569 |

## Scenario — split-pressure-growth

- Description: Force repeated low-bit collisions so extendible hashing must split buckets while cuckoo hashing spends work on displacement and occasional rehashing.
- Operation mix: `puts=11` (`insertions=10`, `updates=1`), `gets=3` (`hits=2`, `misses=1`), `deletes=0` (`hits=0`, `misses=0`)
- Extendible hashing finished at global depth `3` with `6` buckets and load factor `0.8333` after `5` splits / `0` merges and `3` directory growth(s) / `0` directory shrink(s).
- Cuckoo hashing averaged `1.0` rehashes and `11.333` displacements, finishing between capacities `15` and `15`.
- B-tree page baseline finished at height `2` across `4` node(s); at `page_size=512` and `value_bytes=32` the paged snapshot would occupy `2081` bytes with `359` bytes of fixed slack per page.
- Validation: final states matched across `3` deterministic trial(s).

| Trial | Extendible splits | Extendible merges | Peak depth | Peak buckets | Peak directory slots | Cuckoo rehashes | Cuckoo displacements | Cuckoo final capacity | B-tree height | B-tree nodes | B-tree paged bytes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 5 | 0 | 3 | 6 | 8 | 1 | 14 | 15 | 2 | 4 | 2081 |
| 2 | 5 | 0 | 3 | 6 | 8 | 1 | 12 | 15 | 2 | 4 | 2081 |
| 3 | 5 | 0 | 3 | 6 | 8 | 1 | 8 | 15 | 2 | 4 | 2081 |

## Scenario — delete-heavy-churn

- Description: Grow a clustered directory, delete enough keys to trigger extendible merges and shrinks, then repopulate a smaller live set.
- Operation mix: `puts=8` (`insertions=8`, `updates=0`), `gets=2` (`hits=1`, `misses=1`), `deletes=4` (`hits=3`, `misses=1`)
- Extendible hashing finished at global depth `3` with `4` buckets and load factor `0.625` after `4` splits / `1` merges and `4` directory growth(s) / `1` directory shrink(s).
- Cuckoo hashing averaged `0.0` rehashes and `2.333` displacements, finishing between capacities `7` and `7`.
- B-tree page baseline finished at height `2` across `3` node(s); at `page_size=512` and `value_bytes=32` the paged snapshot would occupy `1569` bytes with `359` bytes of fixed slack per page.
- Validation: final states matched across `3` deterministic trial(s).

| Trial | Extendible splits | Extendible merges | Peak depth | Peak buckets | Peak directory slots | Cuckoo rehashes | Cuckoo displacements | Cuckoo final capacity | B-tree height | B-tree nodes | B-tree paged bytes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 4 | 1 | 3 | 4 | 8 | 0 | 4 | 7 | 2 | 3 | 1569 |
| 2 | 4 | 1 | 3 | 4 | 8 | 0 | 2 | 7 | 2 | 3 | 1569 |
| 3 | 4 | 1 | 3 | 4 | 8 | 0 | 1 | 7 | 2 | 3 | 1569 |


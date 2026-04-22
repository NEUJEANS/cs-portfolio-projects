# Fenwick vs Segment Tree Benchmark

- size: 256
- operations per run: 1000
- repeats: 3
- seed: 7
- workload preset: point-set-heavy
- preset summary: Single-index overwrites dominate the workload story.
- query ratio: 0.25
- range-add ratio: 0.2
- point-set ratio: 0.55
- max range width: 12
- correctness verified: True
- faster strategy: range-fenwick
- relative speedup: 1.102x

## Operation mix

- range_sum: 247
- range_add: 200
- point_set: 553

## Strategy summary

| Strategy | Avg seconds | Ops/sec | Range sum avg μs | Range add avg μs | Point set avg μs | Verified |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| range-fenwick | 0.003372 | 296578.96 | 1.747 | 2.453 | 4.214 | True |
| segment-tree | 0.003717 | 269069.06 | 2.4 | 3.332 | 4.211 | True |

## Takeaways

- The benchmark replays the exact same mixed workload through both data structures.
- Query checksums and final totals must match before the timing comparison is considered valid.
- RangeFenwick stays compact and fast for prefix/range-sum style work, while the segment tree provides a useful comparison point for the same update/query mix.

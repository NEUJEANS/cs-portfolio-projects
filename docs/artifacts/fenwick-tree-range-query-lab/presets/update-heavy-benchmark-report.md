# Fenwick vs Segment Tree Benchmark

- size: 256
- operations per run: 1000
- repeats: 3
- seed: 7
- workload preset: update-heavy
- preset summary: Range adds dominate the workload story.
- query ratio: 0.2
- range-add ratio: 0.7
- point-set ratio: 0.1
- max range width: 24
- correctness verified: True
- faster strategy: range-fenwick
- relative speedup: 1.593x

## Operation mix

- range_sum: 203
- range_add: 705
- point_set: 92

## Strategy summary

| Strategy | Avg seconds | Ops/sec | Range sum avg μs | Range add avg μs | Point set avg μs | Verified |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| range-fenwick | 0.002714 | 368505.73 | 1.942 | 2.501 | 4.702 | True |
| segment-tree | 0.004323 | 231298.82 | 3.432 | 4.31 | 4.948 | True |

## Takeaways

- The benchmark replays the exact same mixed workload through both data structures.
- Query checksums and final totals must match before the timing comparison is considered valid.
- RangeFenwick stays compact and fast for prefix/range-sum style work, while the segment tree provides a useful comparison point for the same update/query mix.

# Fenwick vs Segment Tree Benchmark

- size: 256
- operations per run: 1000
- repeats: 3
- seed: 7
- workload preset: query-heavy
- preset summary: Range-sum reads dominate the workload story.
- query ratio: 0.75
- range-add ratio: 0.15
- point-set ratio: 0.1
- max range width: 48
- correctness verified: True
- faster strategy: range-fenwick
- relative speedup: 1.59x

## Operation mix

- range_sum: 762
- range_add: 138
- point_set: 100

## Strategy summary

| Strategy | Avg seconds | Ops/sec | Range sum avg μs | Range add avg μs | Point set avg μs | Verified |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| range-fenwick | 0.002236 | 447145.53 | 1.761 | 2.477 | 4.427 | True |
| segment-tree | 0.003555 | 281261.25 | 3.013 | 4.611 | 4.919 | True |

## Takeaways

- The benchmark replays the exact same mixed workload through both data structures.
- Query checksums and final totals must match before the timing comparison is considered valid.
- RangeFenwick stays compact and fast for prefix/range-sum style work, while the segment tree provides a useful comparison point for the same update/query mix.

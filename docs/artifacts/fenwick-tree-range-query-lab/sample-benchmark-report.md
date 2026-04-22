# Fenwick vs Segment Tree Benchmark

- size: 256
- operations per run: 1000
- repeats: 3
- seed: 7
- correctness verified: True
- faster strategy: range-fenwick
- relative speedup: 1.535x

## Operation mix

- range_sum: 408
- range_add: 408
- point_set: 184

## Strategy summary

| Strategy | Avg seconds | Ops/sec | Range sum avg μs | Range add avg μs | Point set avg μs | Verified |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| range-fenwick | 0.002528 | 395581.67 | 1.713 | 2.33 | 4.203 | True |
| segment-tree | 0.003881 | 257693.68 | 3.021 | 4.162 | 4.52 | True |

## Takeaways

- The benchmark replays the exact same mixed workload through both data structures.
- Query checksums and final totals must match before the timing comparison is considered valid.
- RangeFenwick stays compact and fast for prefix/range-sum style work, while the segment tree provides a useful comparison point for the same update/query mix.

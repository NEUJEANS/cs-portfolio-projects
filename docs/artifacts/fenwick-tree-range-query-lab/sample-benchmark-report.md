# Fenwick vs Segment Tree Benchmark

- size: 256
- operations per run: 1000
- repeats: 3
- seed: 7
- correctness verified: True
- faster strategy: range-fenwick
- relative speedup: 1.538x

## Operation mix

- range_sum: 408
- range_add: 408
- point_set: 184

## Strategy summary

| Strategy | Avg seconds | Ops/sec | Range sum avg μs | Range add avg μs | Point set avg μs | Verified |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| range-fenwick | 0.00271 | 368938.07 | 1.832 | 2.485 | 4.408 | True |
| segment-tree | 0.004169 | 239840.69 | 3.249 | 4.459 | 4.786 | True |

## Takeaways

- The benchmark replays the exact same mixed workload through both data structures.
- Query checksums and final totals must match before the timing comparison is considered valid.
- RangeFenwick stays compact and fast for prefix/range-sum style work, while the segment tree provides a useful comparison point for the same update/query mix.

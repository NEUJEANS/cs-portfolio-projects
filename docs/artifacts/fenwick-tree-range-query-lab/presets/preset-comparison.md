# Fenwick workload preset comparison

- compared presets: balanced, query-heavy, update-heavy, point-set-heavy
- size: 256
- operations per run: 1000
- repeats: 3
- seed: 7
- all correctness checks passed: True
- average Fenwick speedup: 1.469x

## Preset snapshot

| Preset | Mix (Q/A/S) | Dominant op | Faster strategy | Speedup | Fenwick ops/sec | Segment ops/sec | Artifact bundle |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| balanced | 45%/40%/15% | Range sum | range-fenwick | 1.589x | 393522.2 | 247640.54 | [Markdown](../sample-benchmark-report.md) / [SVG](../sample-benchmark-chart.svg) |
| query-heavy | 75%/15%/10% | Range sum | range-fenwick | 1.59x | 447145.53 | 281261.25 | [Markdown](query-heavy-benchmark-report.md) / [SVG](query-heavy-benchmark-chart.svg) |
| update-heavy | 20%/70%/10% | Range add | range-fenwick | 1.593x | 368505.73 | 231298.82 | [Markdown](update-heavy-benchmark-report.md) / [SVG](update-heavy-benchmark-chart.svg) |
| point-set-heavy | 25%/20%/55% | Point set | range-fenwick | 1.102x | 296578.96 | 269069.06 | [Markdown](point-set-heavy-benchmark-report.md) / [SVG](point-set-heavy-benchmark-chart.svg) |

## Operation-level winners

| Operation | Fenwick wins | Segment tree wins |
| --- | ---: | ---: |
| Range sum | 4 | 0 |
| Range add | 4 | 0 |
| Point set | 3 | 1 |

## Takeaways

- Strongest Fenwick edge: `update-heavy` at `1.593x`, where `Range add` dominates the workload.
- Tightest race: `point-set-heavy` at `1.102x`, which is the closest this benchmark pack gets to a near draw.
- Fastest absolute throughput for RangeFenwick: `query-heavy` at `447145.53 ops/sec`.
- Fastest absolute throughput for the segment tree baseline: `query-heavy` at `281261.25 ops/sec`.
- Use the linked per-preset Markdown and SVG artifacts when you want the deeper single-workload breakdown beside this summary dashboard.

# Mini MapReduce benchmark report (plugin-streaming-window: skewed)

- Job: `plugin-streaming-window`
- Plugin: `projects/mini-mapreduce-lab/plugins_streaming_window.py`
- Dataset family: `iot-burst`
- Seed: `42`
- Total records: `240`
- Shard size: `30`
- Reducer counts: `2, 4`
- Available dataset families: `default, iot-burst, live-ops`

## Dataset notes

- Turnstile rush-hour burst: `turnstile-east@2026-04-17T09:10:00Z` dominates this family with both heavier volume and elevated values, so the hottest reducer should read like a lobby ingress spike during class changeover.
- Lobby camera spillover: `camera-lobby@2026-04-17T09:15:00Z` forms a second-tier hotspot right behind the turnstile window, which helps the benchmark tell a fuller story about adjacent systems reacting to the same surge.

## Structured benchmark annotations

### Turnstile rush-hour burst
- Detail: `turnstile-east@2026-04-17T09:10:00Z` dominates this family with both heavier volume and elevated values, so the hottest reducer should read like a lobby ingress spike during class changeover.
- Severity: `risk`
- Hotspot keys: `turnstile-east@2026-04-17T09:10:00Z`
- Takeaway: This turns the plugin into a windowed-streaming case study about burst concentration, not just generic per-key aggregation.

### Lobby camera spillover
- Detail: `camera-lobby@2026-04-17T09:15:00Z` forms a second-tier hotspot right behind the turnstile window, which helps the benchmark tell a fuller story about adjacent systems reacting to the same surge.
- Severity: `watch`
- Hotspot keys: `camera-lobby@2026-04-17T09:15:00Z`
- Takeaway: Keep this note when you want the report to show cross-stream spillover instead of only the single biggest bucket.

## Timing summary

| Reducers | Elapsed (ms) | Shards | Map records | Unique keys | Max reducer records | Skew ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 6.994 | 8 | 240 | 9 | 12 | 1.043 |
| 4 | 8.714 | 8 | 240 | 9 | 8 | 1.391 |

## Heatmap highlights

### Reducers = 2
- Hottest cell: shard `6` → reducer `1` with `3` records across `3` keys
- Coldest cell: shard `0` → reducer `1` with `1` records across `1` keys
- Reducer load stddev: `0.500` records (mean `11.500`)
- Total records per reducer: r0=11, r1=12

| Shard | r0 | r1 |
| --- | ---: | ---: |
| 0 | 2 █████ | 1 ███ |
| 1 | 1 ███ | 1 ███ |
| 2 | 1 ███ | 1 ███ |
| 3 | 1 ███ | 1 ███ |
| 4 | 2 █████ | 2 █████ |
| 5 | 1 ███ | 1 ███ |
| 6 | 2 █████ | 3 ████████ |
| 7 | 1 ███ | 2 █████ |

### Reducers = 4
- Hottest cell: shard `6` → reducer `1` with `3` records across `3` keys
- Coldest cell: shard `0` → reducer `1` with `0` records across `0` keys
- Reducer load stddev: `1.920` records (mean `5.750`)
- Total records per reducer: r0=8, r1=7, r2=3, r3=5

| Shard | r0 | r1 | r2 | r3 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1 ███ | 0 · | 1 ███ | 1 ███ |
| 1 | 1 ███ | 0 · | 0 · | 1 ███ |
| 2 | 1 ███ | 0 · | 0 · | 1 ███ |
| 3 | 1 ███ | 0 · | 0 · | 1 ███ |
| 4 | 2 █████ | 1 ███ | 0 · | 1 ███ |
| 5 | 1 ███ | 1 ███ | 0 · | 0 · |
| 6 | 1 ███ | 3 ████████ | 1 ███ | 0 · |
| 7 | 0 · | 2 █████ | 1 ███ | 0 · |

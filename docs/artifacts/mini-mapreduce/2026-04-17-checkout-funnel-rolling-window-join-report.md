# Mini MapReduce benchmark report (plugin-rolling-window-join: skewed)

- Job: `plugin-rolling-window-join`
- Plugin: `projects/mini-mapreduce-lab/plugins_rolling_window_join.py`
- Dataset family: `checkout-funnel`
- Seed: `42`
- Total records: `240`
- Shard size: `30`
- Reducer counts: `2, 4`
- Available dataset families: `default, checkout-funnel, incident-correlation`

## Dataset notes

- Checkout core backlog: `checkout-core` becomes the dominant join key with the worst pairing lag, so the report looks like a spike of cart updates outrunning payment authorizations during a launch or sale.
- Promo retry spillover: `promo-retry` is the second-tier correlation hotspot behind checkout-core, which helps explain how retries can spread join pressure to a supporting flow instead of one isolated key.

## Structured benchmark annotations

### Checkout core backlog
- Detail: `checkout-core` becomes the dominant join key with the worst pairing lag, so the report looks like a spike of cart updates outrunning payment authorizations during a launch or sale.
- Severity: `risk`
- Hotspot keys: `checkout-core`
- Takeaway: Call out the combination of lower coverage and higher gap when telling the story of queue lag or degraded downstream auth capacity.

### Promo retry spillover
- Detail: `promo-retry` is the second-tier correlation hotspot behind checkout-core, which helps explain how retries can spread join pressure to a supporting flow instead of one isolated key.
- Severity: `watch`
- Hotspot keys: `promo-retry`
- Takeaway: Keep this note when you want the benchmark to feel like a fuller checkout system instead of one synthetic broken key.

## Timing summary

| Reducers | Elapsed (ms) | Shards | Map records | Unique keys | Max reducer records | Skew ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 10.695 | 8 | 240 | 4 | 7 | 1.273 |
| 4 | 9.657 | 8 | 240 | 4 | 7 | 2.545 |

## Heatmap highlights

### Reducers = 2
- Hottest cell: shard `0` → reducer `0` with `1` records across `1` keys
- Coldest cell: shard `0` → reducer `1` with `0` records across `0` keys
- Reducer load stddev: `1.500` records (mean `5.500`)
- Total records per reducer: r0=7, r1=4

| Shard | r0 | r1 |
| --- | ---: | ---: |
| 0 | 1 ████████ | 0 · |
| 1 | 1 ████████ | 0 · |
| 2 | 1 ████████ | 0 · |
| 3 | 1 ████████ | 0 · |
| 4 | 1 ████████ | 1 ████████ |
| 5 | 1 ████████ | 1 ████████ |
| 6 | 1 ████████ | 1 ████████ |
| 7 | 0 · | 1 ████████ |

### Reducers = 4
- Hottest cell: shard `0` → reducer `0` with `1` records across `1` keys
- Coldest cell: shard `0` → reducer `1` with `0` records across `0` keys
- Reducer load stddev: `2.947` records (mean `2.750`)
- Total records per reducer: r0=7, r1=0, r2=0, r3=4

| Shard | r0 | r1 | r2 | r3 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 1 ████████ | 0 · | 0 · | 0 · |
| 1 | 1 ████████ | 0 · | 0 · | 0 · |
| 2 | 1 ████████ | 0 · | 0 · | 0 · |
| 3 | 1 ████████ | 0 · | 0 · | 0 · |
| 4 | 1 ████████ | 0 · | 0 · | 1 ████████ |
| 5 | 1 ████████ | 0 · | 0 · | 1 ████████ |
| 6 | 1 ████████ | 0 · | 0 · | 1 ████████ |
| 7 | 0 · | 0 · | 0 · | 1 ████████ |

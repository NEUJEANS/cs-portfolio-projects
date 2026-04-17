# Mini MapReduce benchmark report (plugin-watermark-late-summary: skewed)

- Job: `plugin-watermark-late-summary`
- Plugin: `projects/mini-mapreduce-lab/plugins_watermark_late_summary.py`
- Dataset family: `sensor-backfill`
- Seed: `42`
- Total records: `240`
- Shard size: `30`
- Reducer counts: `2, 4`
- Available dataset families: `default, sensor-backfill, live-replay`

## Dataset notes

- Meter east replay storm: `meter-east` dominates this family with both accepted and dropped backfills, so the report should look like a utility stream replaying stale packets after a connectivity gap.
- Meter west secondary lag: `meter-west` forms a smaller second-tier late stream behind meter-east, which helps the benchmark tell a richer story about regional spillover instead of a single broken key.

## Structured benchmark annotations

### Meter east replay storm
- Detail: `meter-east` dominates this family with both accepted and dropped backfills, so the report should look like a utility stream replaying stale packets after a connectivity gap.
- Severity: `risk`
- Hotspot keys: `meter-east`
- Takeaway: Call out how the drop rate only climbs after the watermark passes the allowed-lateness boundary for the same windows.

### Meter west secondary lag
- Detail: `meter-west` forms a smaller second-tier late stream behind meter-east, which helps the benchmark tell a richer story about regional spillover instead of a single broken key.
- Severity: `watch`
- Hotspot keys: `meter-west`
- Takeaway: Keep this note when you want a fuller data-engineering narrative instead of focusing only on the worst offender.

## Timing summary

| Reducers | Elapsed (ms) | Shards | Map records | Unique keys | Max reducer records | Skew ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 11.677 | 8 | 240 | 4 | 17 | 1.545 |
| 4 | 11.937 | 8 | 240 | 4 | 12 | 2.182 |

## Heatmap highlights

### Reducers = 2
- Hottest cell: shard `0` → reducer `0` with `3` records across `3` keys
- Coldest cell: shard `5` → reducer `1` with `0` records across `0` keys
- Reducer load stddev: `6.000` records (mean `11.000`)
- Total records per reducer: r0=17, r1=5

| Shard | r0 | r1 |
| --- | ---: | ---: |
| 0 | 3 ████████ | 1 ███ |
| 1 | 3 ████████ | 1 ███ |
| 2 | 3 ████████ | 1 ███ |
| 3 | 3 ████████ | 1 ███ |
| 4 | 2 █████ | 1 ███ |
| 5 | 1 ███ | 0 · |
| 6 | 1 ███ | 0 · |
| 7 | 1 ███ | 0 · |

### Reducers = 4
- Hottest cell: shard `0` → reducer `0` with `2` records across `2` keys
- Coldest cell: shard `0` → reducer `1` with `0` records across `0` keys
- Reducer load stddev: `4.272` records (mean `5.500`)
- Total records per reducer: r0=12, r1=0, r2=5, r3=5

| Shard | r0 | r1 | r2 | r3 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 2 ████████ | 0 · | 1 ████ | 1 ████ |
| 1 | 2 ████████ | 0 · | 1 ████ | 1 ████ |
| 2 | 2 ████████ | 0 · | 1 ████ | 1 ████ |
| 3 | 2 ████████ | 0 · | 1 ████ | 1 ████ |
| 4 | 1 ████ | 0 · | 1 ████ | 1 ████ |
| 5 | 1 ████ | 0 · | 0 · | 0 · |
| 6 | 1 ████ | 0 · | 0 · | 0 · |
| 7 | 1 ████ | 0 · | 0 · | 0 · |

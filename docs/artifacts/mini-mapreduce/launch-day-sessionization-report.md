# Mini MapReduce benchmark report (plugin-sessionization: skewed)

- Job: `plugin-sessionization`
- Plugin: `projects/mini-mapreduce-lab/plugins_sessionization.py`
- Dataset family: `launch-day`
- Seed: `42`
- Total records: `240`
- Shard size: `30`
- Reducer counts: `2, 4`
- Available dataset families: `default, exam-revision, launch-day`

## Dataset notes

- Release lead war room: `release-lead` dominates this family with back-to-back dashboard, deploy, and rollback visits, so the hottest reducer should look like one operator repeatedly re-entering a release war room.
- QA desk verification loop: `qa-desk` forms a second-tier hotspot behind the release lead, which helps the report show supporting verification traffic instead of a single isolated key.

## Structured benchmark annotations

### Release lead war room
- Detail: `release-lead` dominates this family with back-to-back dashboard, deploy, and rollback visits, so the hottest reducer should look like one operator repeatedly re-entering a release war room.
- Severity: `risk`
- Hotspot keys: `release-lead`
- Takeaway: This turns the plugin into a product-analytics case study about launch-day behavior rather than generic score aggregation.

### QA desk verification loop
- Detail: `qa-desk` forms a second-tier hotspot behind the release lead, which helps the report show supporting verification traffic instead of a single isolated key.
- Severity: `watch`
- Hotspot keys: `qa-desk`
- Takeaway: Keep this note when you want a fuller multi-role launch narrative in the benchmark report.

## Timing summary

| Reducers | Elapsed (ms) | Shards | Map records | Unique keys | Max reducer records | Skew ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 6.283 | 8 | 240 | 4 | 20 | 1.538 |
| 4 | 6.07 | 8 | 240 | 4 | 20 | 3.077 |

## Heatmap highlights

### Reducers = 2
- Hottest cell: shard `0` → reducer `0` with `3` records across `3` keys
- Coldest cell: shard `6` → reducer `1` with `0` records across `0` keys
- Reducer load stddev: `7.000` records (mean `13.000`)
- Total records per reducer: r0=20, r1=6

| Shard | r0 | r1 |
| --- | ---: | ---: |
| 0 | 3 ████████ | 1 ███ |
| 1 | 3 ████████ | 1 ███ |
| 2 | 3 ████████ | 1 ███ |
| 3 | 3 ████████ | 1 ███ |
| 4 | 3 ████████ | 1 ███ |
| 5 | 2 █████ | 1 ███ |
| 6 | 2 █████ | 0 · |
| 7 | 1 ███ | 0 · |

### Reducers = 4
- Hottest cell: shard `0` → reducer `0` with `3` records across `3` keys
- Coldest cell: shard `0` → reducer `1` with `0` records across `0` keys
- Reducer load stddev: `8.170` records (mean `6.500`)
- Total records per reducer: r0=20, r1=0, r2=0, r3=6

| Shard | r0 | r1 | r2 | r3 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 3 ████████ | 0 · | 0 · | 1 ███ |
| 1 | 3 ████████ | 0 · | 0 · | 1 ███ |
| 2 | 3 ████████ | 0 · | 0 · | 1 ███ |
| 3 | 3 ████████ | 0 · | 0 · | 1 ███ |
| 4 | 3 ████████ | 0 · | 0 · | 1 ███ |
| 5 | 2 █████ | 0 · | 0 · | 1 ███ |
| 6 | 2 █████ | 0 · | 0 · | 0 · |
| 7 | 1 ███ | 0 · | 0 · | 0 · |

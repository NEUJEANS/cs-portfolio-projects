# Mini MapReduce benchmark report (plugin-service-latency: skewed)

- Job: `plugin-service-latency`
- Plugin: `projects/mini-mapreduce-lab/plugins_service_latency.py`
- Dataset family: `incident-spike`
- Seed: `42`
- Total records: `240`
- Shard size: `30`
- Reducer counts: `2, 4`
- Available dataset families: `default, incident-spike, batch-window`

## Dataset notes

- Auth gateway timeout storm: `auth-gateway` dominates this family with elevated latency, so the hottest reducer should look like an outage-era timeout storm concentrated around one service.
- Session cache spillover: `session-cache` forms the second-tier hotspot behind the auth gateway, which helps tell a broader bottleneck story about downstream spillover instead of a single bad node.
- Profile path cool lane: `profile-read` stays comparatively cool, so it works as a low-priority contrast point or a card to collapse in tighter portfolio reports.

## Structured benchmark annotations

### Auth gateway timeout storm
- Detail: `auth-gateway` dominates this family with elevated latency, so the hottest reducer should look like an outage-era timeout storm concentrated around one service.
- Severity: `risk`
- Hotspot keys: `auth-gateway`
- Takeaway: Call out the gap between average and p95 latency here to explain why long-tail spikes matter during incidents.

### Session cache spillover
- Detail: `session-cache` forms the second-tier hotspot behind the auth gateway, which helps tell a broader bottleneck story about downstream spillover instead of a single bad node.
- Severity: `watch`
- Hotspot keys: `session-cache`
- Takeaway: Keep this annotation when you want a fuller causal narrative about cascading latency during the same incident.

### Profile path cool lane
- Detail: `profile-read` stays comparatively cool, so it works as a low-priority contrast point or a card to collapse in tighter portfolio reports.
- Severity: `info`
- Hotspot keys: `profile-read`
- Takeaway: Use annotation filtering when you want the report to focus only on the riskiest paths.

## Timing summary

| Reducers | Elapsed (ms) | Shards | Map records | Unique keys | Max reducer records | Skew ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 7.376 | 8 | 240 | 4 | 14 | 1.077 |
| 4 | 5.581 | 8 | 240 | 4 | 14 | 2.154 |

## Heatmap highlights

### Reducers = 2
- Hottest cell: shard `2` → reducer `0` with `2` records across `2` keys
- Coldest cell: shard `0` → reducer `0` with `0` records across `0` keys
- Reducer load stddev: `1.000` records (mean `13.000`)
- Total records per reducer: r0=12, r1=14

| Shard | r0 | r1 |
| --- | ---: | ---: |
| 0 | 0 · | 1 ████ |
| 1 | 0 · | 1 ████ |
| 2 | 2 ████████ | 2 ████████ |
| 3 | 2 ████████ | 2 ████████ |
| 4 | 2 ████████ | 2 ████████ |
| 5 | 2 ████████ | 2 ████████ |
| 6 | 2 ████████ | 2 ████████ |
| 7 | 2 ████████ | 2 ████████ |

### Reducers = 4
- Hottest cell: shard `2` → reducer `0` with `2` records across `2` keys
- Coldest cell: shard `0` → reducer `0` with `0` records across `0` keys
- Reducer load stddev: `6.538` records (mean `6.500`)
- Total records per reducer: r0=12, r1=14, r2=0, r3=0

| Shard | r0 | r1 | r2 | r3 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 0 · | 1 ████ | 0 · | 0 · |
| 1 | 0 · | 1 ████ | 0 · | 0 · |
| 2 | 2 ████████ | 2 ████████ | 0 · | 0 · |
| 3 | 2 ████████ | 2 ████████ | 0 · | 0 · |
| 4 | 2 ████████ | 2 ████████ | 0 · | 0 · |
| 5 | 2 ████████ | 2 ████████ | 0 · | 0 · |
| 6 | 2 ████████ | 2 ████████ | 0 · | 0 · |
| 7 | 2 ████████ | 2 ████████ | 0 · | 0 · |

# Mini MapReduce benchmark report (plugin-average-score: skewed)

- Job: `plugin-average-score`
- Plugin: `projects/mini-mapreduce-lab/plugins_average_score.py`
- Dataset family: `project-week`
- Seed: `42`
- Total records: `240`
- Shard size: `30`
- Reducer counts: `2, 4`
- Available dataset families: `default, exam-cram, project-week`

## Dataset notes

- Demo-day crunch hotspot: `demo-day-core` is the main hotspot here, with integration and feature tails behind it, so you can narrate the skew as a deadline-driven project crunch.
- Integration review backlog: The `integration-*` keys form a second-tier hotspot behind the demo-day core, which makes a good reviewer note when you want to talk about handoff queues instead of only the primary spike.
- Feature-lane tail: The `feature-*` keys stay spread out and comparatively cooler, so they are useful as a low-priority reviewer note but often safe to collapse in tighter portfolio reports.

## Structured benchmark annotations

### Demo-day crunch hotspot
- Detail: `demo-day-core` is the main hotspot here, with integration and feature tails behind it, so you can narrate the skew as a deadline-driven project crunch.
- Severity: `risk`
- Hotspot keys: `demo-day-core, integration-0, feature-0`
- Takeaway: This slice is meant to read like a real project-week bottleneck where one squad absorbs the final demo push.

### Integration review backlog
- Detail: The `integration-*` keys form a second-tier hotspot behind the demo-day core, which makes a good reviewer note when you want to talk about handoff queues instead of only the primary spike.
- Severity: `watch`
- Hotspot keys: `integration-0, integration-1, integration-2`
- Takeaway: Keep this card when you want a fuller systems story about follow-on bottlenecks after the main project crunch.

### Feature-lane tail
- Detail: The `feature-*` keys stay spread out and comparatively cooler, so they are useful as a low-priority reviewer note but often safe to collapse in tighter portfolio reports.
- Severity: `info`
- Hotspot keys: `feature-0, feature-1`
- Takeaway: Use annotation filters or overflow summaries when you want to hide softer follow-up notes and keep the report focused on the highest-risk queues.

## Timing summary

| Reducers | Elapsed (ms) | Shards | Map records | Unique keys | Max reducer records | Skew ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 5.066 | 8 | 240 | 21 | 71 | 1.34 |
| 4 | 5.225 | 8 | 240 | 21 | 40 | 1.509 |

## Heatmap highlights

### Reducers = 2
- Hottest cell: shard `2` → reducer `0` with `10` records across `10` keys
- Coldest cell: shard `5` → reducer `1` with `3` records across `3` keys
- Reducer load stddev: `18.000` records (mean `53.000`)
- Total records per reducer: r0=71, r1=35

| Shard | r0 | r1 |
| --- | ---: | ---: |
| 0 | 8 ██████ | 6 █████ |
| 1 | 9 ███████ | 4 ███ |
| 2 | 10 ████████ | 4 ███ |
| 3 | 8 ██████ | 4 ███ |
| 4 | 10 ████████ | 5 ████ |
| 5 | 7 ██████ | 3 ██ |
| 6 | 9 ███████ | 5 ████ |
| 7 | 10 ████████ | 4 ███ |

### Reducers = 4
- Hottest cell: shard `4` → reducer `0` with `7` records across `7` keys
- Coldest cell: shard `1` → reducer `1` with `1` records across `1` keys
- Reducer load stddev: `9.552` records (mean `26.500`)
- Total records per reducer: r0=40, r1=18, r2=31, r3=17

| Shard | r0 | r1 | r2 | r3 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 4 █████ | 3 ███ | 4 █████ | 3 ███ |
| 1 | 4 █████ | 1 █ | 5 ██████ | 3 ███ |
| 2 | 6 ███████ | 2 ██ | 4 █████ | 2 ██ |
| 3 | 5 ██████ | 2 ██ | 3 ███ | 2 ██ |
| 4 | 7 ████████ | 3 ███ | 3 ███ | 2 ██ |
| 5 | 4 █████ | 2 ██ | 3 ███ | 1 █ |
| 6 | 5 ██████ | 2 ██ | 4 █████ | 3 ███ |
| 7 | 5 ██████ | 3 ███ | 5 ██████ | 1 █ |

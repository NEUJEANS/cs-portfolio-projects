# Mini MapReduce plugin doc: `plugin-watermark-late-summary`

## Snapshot

- Plugin path: `projects/mini-mapreduce-lab/plugins_watermark_late_summary.py`
- Summary: Watermark-aware late-event summary plugin for out-of-order stream-processing demos.
- Dataset families: `default, sensor-backfill, live-replay`
- Catalog badges: `5 hooks` · `3 dataset families` · `commit pinned` · `github linked`
- Repository commit: `8e9ad856e42484ad83d46bfe15fe4f0823004f77`
- Catalog index: [plugin catalog](../plugin-catalog.md)
- Alternate format: [HTML](plugin-watermark-late-summary.html)

## Hook summary

| Hook | Export | Signature | Details | Source |
| --- | --- | --- | --- | --- |
| Mapper | `plugins_watermark_late_summary.map_records` | `map_records(lines)` | Emit per-stream event batches from stream,event_time,arrival_time,value rows.<br>line 136<br>anchor `plugins_watermark_late_summary.py#L136-L147` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L136-L147)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/8e9ad856e42484ad83d46bfe15fe4f0823004f77/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L136-L147) |
| Reducer | `plugins_watermark_late_summary.reduce_key` | `reduce_key(key, values)` | Summarize watermark-aware acceptance, late updates, and dropped events for one stream.<br>line 155<br>anchor `plugins_watermark_late_summary.py#L155-L223` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L155-L223)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/8e9ad856e42484ad83d46bfe15fe4f0823004f77/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L155-L223) |
| Combiner | `plugins_watermark_late_summary.combine_values` | `combine_values(_key, values)` | Keep shard-local stream event batches JSON-safe before watermark evaluation.<br>line 150<br>anchor `plugins_watermark_late_summary.py#L150-L152` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L150-L152)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/8e9ad856e42484ad83d46bfe15fe4f0823004f77/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L150-L152) |
| Benchmark generator | `plugins_watermark_late_summary.benchmark_records` | `benchmark_records(scenario, records, seed, dataset_family='default')` | Generate deterministic out-of-order event streams for watermark-summary demos.<br>line 266<br>anchor `plugins_watermark_late_summary.py#L266-L341` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L266-L341)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/8e9ad856e42484ad83d46bfe15fe4f0823004f77/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L266-L341) |
| Benchmark note hook | `plugins_watermark_late_summary.benchmark_notes` | `benchmark_notes(scenario, dataset_family='default')` | Describe the intended late-event hotspot story for each synthetic family.<br>line 344<br>anchor `plugins_watermark_late_summary.py#L344-L413` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L344-L413)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/8e9ad856e42484ad83d46bfe15fe4f0823004f77/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L344-L413) |

## Hook source excerpts

### Mapper: `plugins_watermark_late_summary.map_records`

- Summary: Emit per-stream event batches from stream,event_time,arrival_time,value rows.
- Source line: `136`
- Source anchor: `plugins_watermark_late_summary.py#L136-L147`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L136-L147>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/8e9ad856e42484ad83d46bfe15fe4f0823004f77/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L136-L147>

```python
def map_records(lines):
    """Emit per-stream event batches from stream,event_time,arrival_time,value rows."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        stream, event_at, arrived_at, value = [part.strip() for part in stripped.split(",", maxsplit=3)]
        yield stream.lower(), {
            "event_at": _isoformat_z(_parse_timestamp(event_at)),
            "arrived_at": _isoformat_z(_parse_timestamp(arrived_at)),
            "value": round(float(value), 3),
        }
```

### Reducer: `plugins_watermark_late_summary.reduce_key`

- Summary: Summarize watermark-aware acceptance, late updates, and dropped events for one stream.
- Source line: `155`
- Source anchor: `plugins_watermark_late_summary.py#L155-L223`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L155-L223>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/8e9ad856e42484ad83d46bfe15fe4f0823004f77/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L155-L223>

```python
def reduce_key(key, values):
    """Summarize watermark-aware acceptance, late updates, and dropped events for one stream."""
    merged = _merge_event_batches(values)
    events = merged["events"]
    windows = {}
    max_seen_event_time = None
    first_arrival_at = None
    last_arrival_at = None
    max_watermark_gap_minutes = 0.0
    late_events_seen = 0

    for item in events:
        event_at = _parse_timestamp(item["event_at"])
        arrived_at = _parse_timestamp(item["arrived_at"])
        value = float(item["value"])
        if first_arrival_at is None or arrived_at < first_arrival_at:
            first_arrival_at = arrived_at
        if last_arrival_at is None or arrived_at > last_arrival_at:
            last_arrival_at = arrived_at

        watermark_before = _watermark_for(max_seen_event_time)
        window_start = _window_start(event_at)
        window_key = _isoformat_z(window_start)
        summary = windows.setdefault(window_key, _new_window_summary(window_start))
        window_close_at = _parse_timestamp(summary["window_close_at"])
        late = watermark_before is not None and event_at < watermark_before
        dropped = watermark_before is not None and watermark_before > window_close_at
        if late and watermark_before is not None:
            late_events_seen += 1
            max_watermark_gap_minutes = max(
                max_watermark_gap_minutes,
                round((watermark_before - event_at).total_seconds() / 60, 3),
            )

        _update_window_summary(summary, event_at=event_at, arrived_at=arrived_at, value=value, late=late, dropped=dropped)
        max_seen_event_time = event_at if max_seen_event_time is None else max(max_seen_event_time, event_at)

    finalized_windows = [_finalize_window_summary(windows[key]) for key in sorted(windows)]
    accepted_events = sum(item["accepted_events"] for item in finalized_windows)
    on_time_events = sum(item["on_time_events"] for item in finalized_windows)
    late_accepted_events = sum(item["late_accepted_events"] for item in finalized_windows)
    dropped_late_events = sum(item["dropped_late_events"] for item in finalized_windows)
    total_events_seen = sum(item["events_seen"] for item in finalized_windows)
    hottest_window = max(
        finalized_windows,
        key=lambda item: (item["late_accepted_events"] + item["dropped_late_events"], item["accepted_events"], item["window_start"]),
        default=None,
    )
    return {
        "stream": key,
        "window_count": len(finalized_windows),
        "total_events_seen": total_events_seen,
        "accepted_events": accepted_events,
        "on_time_events": on_time_events,
        "late_events_seen": late_events_seen,
        "late_accepted_events": late_accepted_events,
        "dropped_late_events": dropped_late_events,
        "late_acceptance_rate": round(late_accepted_events / accepted_events, 3) if accepted_events else 0.0,
        "drop_rate": round(dropped_late_events / total_events_seen, 3) if total_events_seen else 0.0,
        "first_arrival_at": _isoformat_z(first_arrival_at) if first_arrival_at else None,
        "last_arrival_at": _isoformat_z(last_arrival_at) if last_arrival_at else None,
        "final_watermark": _isoformat_z(_watermark_for(max_seen_event_time)) if max_seen_event_time else None,
        "max_watermark_gap_minutes": round(max_watermark_gap_minutes, 3),
        "hottest_window_start": hottest_window["window_start"] if hottest_window else None,
        "hottest_window_late_events": (
            hottest_window["late_accepted_events"] + hottest_window["dropped_late_events"]
        ) if hottest_window else 0,
        "windows": finalized_windows,
    }
```

### Combiner: `plugins_watermark_late_summary.combine_values`

- Summary: Keep shard-local stream event batches JSON-safe before watermark evaluation.
- Source line: `150`
- Source anchor: `plugins_watermark_late_summary.py#L150-L152`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L150-L152>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/8e9ad856e42484ad83d46bfe15fe4f0823004f77/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L150-L152>

```python
def combine_values(_key, values):
    """Keep shard-local stream event batches JSON-safe before watermark evaluation."""
    return {"events": sorted(values, key=lambda event: (event["arrived_at"], event["event_at"], event["value"]))}
```

### Benchmark generator: `plugins_watermark_late_summary.benchmark_records`

- Summary: Generate deterministic out-of-order event streams for watermark-summary demos.
- Source line: `266`
- Source anchor: `plugins_watermark_late_summary.py#L266-L341`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L266-L341>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/8e9ad856e42484ad83d46bfe15fe4f0823004f77/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L266-L341>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic out-of-order event streams for watermark-summary demos."""
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)

    families = {
        "default": {
            "balanced": [
                {"stream": "sensor-alpha", "weight": 1.0, "window_offsets": [0, 5, 10], "base_value": 20.5, "spread": 0.9, "drift": 0.2, "late_offsets": [5]},
                {"stream": "sensor-beta", "weight": 1.0, "window_offsets": [0, 10, 15], "base_value": 22.0, "spread": 1.0, "drift": 0.2, "late_offsets": [10]},
                {"stream": "sensor-gamma", "weight": 1.0, "window_offsets": [5, 10, 15], "base_value": 19.4, "spread": 0.8, "drift": 0.2, "late_offsets": [5]},
                {"stream": "sensor-delta", "weight": 1.0, "window_offsets": [0, 5, 15], "base_value": 21.2, "spread": 0.9, "drift": 0.1},
            ],
            "skewed": [
                {"stream": "sensor-alpha", "weight": 3.6, "window_offsets": [5, 10, 10], "base_value": 25.6, "spread": 1.2, "drift": 0.4, "late_offsets": [5, 10], "drop_offsets": [5], "hotspot_offsets": [10], "hotspot_bonus": 3.8},
                {"stream": "sensor-beta", "weight": 1.0, "window_offsets": [0, 10, 15], "base_value": 22.4, "spread": 0.9, "drift": 0.2, "late_offsets": [10]},
                {"stream": "sensor-gamma", "weight": 0.9, "window_offsets": [0, 5, 15], "base_value": 19.8, "spread": 0.8, "drift": 0.1},
                {"stream": "sensor-delta", "weight": 0.8, "window_offsets": [5, 15, 20], "base_value": 21.1, "spread": 0.9, "drift": 0.2},
            ],
        },
        "sensor-backfill": {
            "balanced": [
                {"stream": "meter-east", "weight": 1.1, "window_offsets": [0, 5, 10], "base_value": 34.5, "spread": 1.1, "drift": 0.3, "late_offsets": [5]},
                {"stream": "meter-west", "weight": 1.0, "window_offsets": [0, 10, 15], "base_value": 33.8, "spread": 1.0, "drift": 0.2, "late_offsets": [10]},
                {"stream": "pipeline-north", "weight": 1.0, "window_offsets": [5, 10, 20], "base_value": 31.2, "spread": 1.0, "drift": 0.2, "late_offsets": [5]},
                {"stream": "pipeline-south", "weight": 0.9, "window_offsets": [0, 15, 20], "base_value": 32.1, "spread": 0.9, "drift": 0.2},
            ],
            "skewed": [
                {"stream": "meter-east", "weight": 4.0, "window_offsets": [5, 10, 15], "base_value": 39.2, "spread": 1.4, "drift": 0.5, "late_offsets": [5, 10], "drop_offsets": [5, 10], "hotspot_offsets": [10], "hotspot_bonus": 6.2},
                {"stream": "meter-west", "weight": 1.2, "window_offsets": [0, 10, 20], "base_value": 35.1, "spread": 1.1, "drift": 0.2, "late_offsets": [10]},
                {"stream": "pipeline-north", "weight": 1.0, "window_offsets": [5, 15, 20], "base_value": 31.6, "spread": 1.0, "drift": 0.2},
                {"stream": "pipeline-south", "weight": 0.8, "window_offsets": [0, 15, 25], "base_value": 32.4, "spread": 0.9, "drift": 0.2},
            ],
        },
        "live-replay": {
            "balanced": [
                {"stream": "chat-ingest", "weight": 1.0, "window_offsets": [0, 5, 10], "base_value": 44.0, "spread": 1.2, "drift": 0.3, "late_offsets": [5]},
                {"stream": "reaction-fanout", "weight": 1.0, "window_offsets": [0, 10, 15], "base_value": 41.5, "spread": 1.1, "drift": 0.3, "late_offsets": [10]},
                {"stream": "presence-sync", "weight": 1.0, "window_offsets": [5, 10, 20], "base_value": 37.2, "spread": 1.0, "drift": 0.2},
                {"stream": "moderation-queue", "weight": 1.0, "window_offsets": [0, 15, 20], "base_value": 40.1, "spread": 1.1, "drift": 0.3, "late_offsets": [15]},
            ],
            "skewed": [
                {"stream": "moderation-queue", "weight": 3.9, "window_offsets": [15, 20, 20], "base_value": 50.3, "spread": 1.6, "drift": 0.6, "late_offsets": [15, 20], "drop_offsets": [15], "hotspot_offsets": [20], "hotspot_bonus": 7.1},
                {"stream": "reaction-fanout", "weight": 1.5, "window_offsets": [10, 15, 20], "base_value": 43.4, "spread": 1.2, "drift": 0.3, "late_offsets": [15]},
                {"stream": "chat-ingest", "weight": 1.0, "window_offsets": [0, 10, 25], "base_value": 44.2, "spread": 1.1, "drift": 0.2},
                {"stream": "presence-sync", "weight": 0.9, "window_offsets": [5, 15, 25], "base_value": 37.8, "spread": 1.0, "drift": 0.2},
            ],
        },
    }
    if dataset_family not in families or scenario not in families[dataset_family]:
        raise ValueError(f"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}")

    profiles = families[dataset_family][scenario]
    counts = _allocate_counts(records, [profile["weight"] for profile in profiles])
    lines = []
    for profile, count in zip(profiles, counts):
        lines.extend(
            _generate_stream_events(
                stream=profile["stream"],
                count=count,
                base_time=base_time,
                window_offsets=profile["window_offsets"],
                base_value=profile["base_value"],
                spread=profile["spread"],
                drift=profile["drift"],
                rng=rng,
                late_window_offsets=profile.get("late_offsets"),
                drop_window_offsets=profile.get("drop_offsets"),
                hotspot_window_offsets=profile.get("hotspot_offsets"),
                hotspot_bonus=profile.get("hotspot_bonus", 0.0),
            )
        )
    lines.sort(key=lambda line: tuple(line.split(",", maxsplit=3)[1:3]))
    return lines[:records]
```

### Benchmark note hook: `plugins_watermark_late_summary.benchmark_notes`

- Summary: Describe the intended late-event hotspot story for each synthetic family.
- Source line: `344`
- Source anchor: `plugins_watermark_late_summary.py#L344-L413`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L344-L413>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/8e9ad856e42484ad83d46bfe15fe4f0823004f77/projects/mini-mapreduce-lab/plugins_watermark_late_summary.py#L344-L413>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended late-event hotspot story for each synthetic family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Mostly on-time telemetry baseline",
                "detail": "The default balanced family keeps late updates mild and spread across four streams, so the report should read like a healthy watermark configuration rather than an incident.",
                "severity": "info",
                "takeaway": "Use this as the before state for explaining why a single stream with repeated backfills changes both lateness and drop rates.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Sensor alpha late-event hotspot",
                "detail": "`sensor-alpha` is intentionally overloaded with backfilled windows, so the hottest reducer should show one stream dominating both late-accepted updates and dropped events.",
                "severity": "watch",
                "hotspot_keys": ["sensor-alpha"],
                "takeaway": "This is the simplest portfolio story for explaining event time, watermarks, and allowed lateness without needing a full streaming framework.",
            },
        ],
        ("balanced", "sensor-backfill"): [
            {
                "title": "Routine meter replays",
                "detail": "The balanced sensor-backfill family makes every stream tolerate a few delayed packets, so the output reads like normal AMI backfill handling instead of a broken ingest pipeline.",
                "severity": "info",
                "takeaway": "Good for showing how watermark-aware summaries stay useful even when the late path is healthy and controlled.",
            },
        ],
        ("skewed", "sensor-backfill"): [
            {
                "title": "Meter east replay storm",
                "detail": "`meter-east` dominates this family with both accepted and dropped backfills, so the report should look like a utility stream replaying stale packets after a connectivity gap.",
                "severity": "risk",
                "hotspot_keys": ["meter-east"],
                "takeaway": "Call out how the drop rate only climbs after the watermark passes the allowed-lateness boundary for the same windows.",
            },
            {
                "title": "Meter west secondary lag",
                "detail": "`meter-west` forms a smaller second-tier late stream behind meter-east, which helps the benchmark tell a richer story about regional spillover instead of a single broken key.",
                "severity": "watch",
                "hotspot_keys": ["meter-west"],
                "takeaway": "Keep this note when you want a fuller data-engineering narrative instead of focusing only on the worst offender.",
            },
        ],
        ("balanced", "live-replay"): [
            {
                "title": "Steady live-ops baseline",
                "detail": "The balanced live-replay family keeps ingest, reactions, presence, and moderation close enough that the report reads like a normal stream-processing pipeline with occasional harmless replays.",
                "severity": "info",
                "takeaway": "Use this as the calm baseline before showing how moderation replays create visible watermark pressure.",
            },
        ],
        ("skewed", "live-replay"): [
            {
                "title": "Moderation replay pile-up",
                "detail": "`moderation-queue` becomes the obvious hotspot here with repeated stale replays, so the watermark summary looks like one downstream queue absorbing late chat events during a live launch.",
                "severity": "risk",
                "hotspot_keys": ["moderation-queue"],
                "takeaway": "This turns the plugin into a streaming-systems case study about out-of-order handling instead of only fixed windows or batch reducers.",
            },
            {
                "title": "Reaction fanout echo",
                "detail": "`reaction-fanout` is the supporting late stream behind moderation, which helps explain how one replay wave can surface in multiple downstream consumers.",
                "severity": "watch",
                "hotspot_keys": ["reaction-fanout"],
                "takeaway": "Keep this annotation when you want the report to highlight pipeline-wide replay propagation.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```

# Mini MapReduce plugin doc: `plugin-streaming-window`

## Snapshot

- Plugin path: `projects/mini-mapreduce-lab/plugins_streaming_window.py`
- Summary: Streaming-window aggregation plugin for telemetry-style benchmark demos.
- Dataset families: `default, iot-burst, live-ops`
- Catalog badges: `5 hooks` · `3 dataset families` · `commit pinned` · `github linked`
- Repository commit: `2332425c37ad2eb7d0399cb11e91a2354e189d22`
- Catalog index: [plugin catalog](../plugin-catalog.md)
- Alternate format: [HTML](plugin-streaming-window.html)

## Hook summary

| Hook | Export | Signature | Details | Source |
| --- | --- | --- | --- | --- |
| Mapper | `plugins_streaming_window.map_records` | `map_records(lines)` | Emit per-stream, per-window summary objects from stream,timestamp,value rows.<br>line 73<br>anchor `plugins_streaming_window.py#L73-L90` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90) |
| Reducer | `plugins_streaming_window.reduce_key` | `reduce_key(key, values)` | Return window-level count, range, and rate metrics for one stream bucket.<br>line 98<br>anchor `plugins_streaming_window.py#L98-L123` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123) |
| Combiner | `plugins_streaming_window.combine_values` | `combine_values(_key, values)` | Merge shard-local window summaries before the final reduce step.<br>line 93<br>anchor `plugins_streaming_window.py#L93-L95` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95) |
| Benchmark generator | `plugins_streaming_window.benchmark_records` | `benchmark_records(scenario, records, seed, dataset_family='default')` | Generate deterministic windowed telemetry fixtures for benchmark scenarios.<br>line 139<br>anchor `plugins_streaming_window.py#L139-L212` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212) |
| Benchmark note hook | `plugins_streaming_window.benchmark_notes` | `benchmark_notes(scenario, dataset_family='default')` | Describe the intended hot windows and portfolio story for each family.<br>line 215<br>anchor `plugins_streaming_window.py#L215-L284` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284) |

## Hook source excerpts

### Mapper: `plugins_streaming_window.map_records`

- Summary: Emit per-stream, per-window summary objects from stream,timestamp,value rows.
- Source line: `73`
- Source anchor: `plugins_streaming_window.py#L73-L90`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L73-L90>

```python
def map_records(lines):
    """Emit per-stream, per-window summary objects from stream,timestamp,value rows."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        stream, timestamp, value = [part.strip() for part in stripped.split(",", maxsplit=2)]
        parsed_timestamp = _parse_timestamp(timestamp)
        window_start = _window_start(parsed_timestamp)
        numeric_value = round(float(value), 3)
        yield f"{stream.lower()}@{_isoformat_z(window_start)}", {
            "count": 1,
            "sum": numeric_value,
            "min": numeric_value,
            "max": numeric_value,
            "first_event_at": _isoformat_z(parsed_timestamp),
            "last_event_at": _isoformat_z(parsed_timestamp),
        }
```

### Reducer: `plugins_streaming_window.reduce_key`

- Summary: Return window-level count, range, and rate metrics for one stream bucket.
- Source line: `98`
- Source anchor: `plugins_streaming_window.py#L98-L123`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L98-L123>

```python
def reduce_key(key, values):
    """Return window-level count, range, and rate metrics for one stream bucket."""
    stream, window_start = _split_window_key(key)
    merged = _merge_window_values(values)
    count = int(merged["count"])
    first_event_at = merged["first_event_at"]
    last_event_at = merged["last_event_at"]
    span_minutes = 0.0
    if first_event_at and last_event_at:
        span_minutes = round(
            (_parse_timestamp(last_event_at) - _parse_timestamp(first_event_at)).total_seconds() / 60,
            3,
        )
    return {
        "stream": stream,
        "window_start": window_start,
        "window_end": _isoformat_z(_parse_timestamp(window_start) + timedelta(minutes=WINDOW_MINUTES)),
        "count": count,
        "avg_value": round(float(merged["sum"]) / count, 3) if count else 0.0,
        "min_value": round(float(merged["min"]), 3) if count else 0.0,
        "max_value": round(float(merged["max"]), 3) if count else 0.0,
        "event_rate_per_minute": round(count / WINDOW_MINUTES, 3) if count else 0.0,
        "first_event_at": first_event_at,
        "last_event_at": last_event_at,
        "span_minutes": span_minutes,
    }
```

### Combiner: `plugins_streaming_window.combine_values`

- Summary: Merge shard-local window summaries before the final reduce step.
- Source line: `93`
- Source anchor: `plugins_streaming_window.py#L93-L95`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L93-L95>

```python
def combine_values(_key, values):
    """Merge shard-local window summaries before the final reduce step."""
    return _merge_window_values(values)
```

### Benchmark generator: `plugins_streaming_window.benchmark_records`

- Summary: Generate deterministic windowed telemetry fixtures for benchmark scenarios.
- Source line: `139`
- Source anchor: `plugins_streaming_window.py#L139-L212`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L139-L212>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic windowed telemetry fixtures for benchmark scenarios."""
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)

    families = {
        "default": {
            "balanced": [
                {"stream": "sensor-alpha", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 21.5, "spread": 1.1, "drift": 0.3},
                {"stream": "sensor-beta", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 23.2, "spread": 1.0, "drift": 0.2},
                {"stream": "sensor-gamma", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 19.8, "spread": 1.2, "drift": 0.4},
                {"stream": "sensor-delta", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 24.0, "spread": 1.1, "drift": 0.2},
            ],
            "skewed": [
                {"stream": "sensor-alpha", "weight": 3.6, "window_offsets": [5, 5, 10], "base_value": 27.5, "spread": 1.4, "drift": 0.5, "hotspot_offsets": [5], "hotspot_bonus": 4.5},
                {"stream": "sensor-beta", "weight": 1.0, "window_offsets": [0, 10, 15], "base_value": 23.0, "spread": 1.1, "drift": 0.2},
                {"stream": "sensor-gamma", "weight": 0.9, "window_offsets": [0, 10, 15], "base_value": 20.1, "spread": 1.2, "drift": 0.3},
                {"stream": "sensor-delta", "weight": 0.8, "window_offsets": [5, 15], "base_value": 22.7, "spread": 1.0, "drift": 0.3},
            ],
        },
        "iot-burst": {
            "balanced": [
                {"stream": "turnstile-east", "weight": 1.1, "window_offsets": [5, 10, 15], "base_value": 31.0, "spread": 1.5, "drift": 0.6},
                {"stream": "camera-lobby", "weight": 1.0, "window_offsets": [5, 10, 15], "base_value": 28.5, "spread": 1.3, "drift": 0.4},
                {"stream": "hvac-north", "weight": 1.0, "window_offsets": [0, 10, 20], "base_value": 24.3, "spread": 1.0, "drift": 0.2},
                {"stream": "badge-reader", "weight": 0.9, "window_offsets": [0, 5, 15], "base_value": 26.0, "spread": 1.1, "drift": 0.3},
            ],
            "skewed": [
                {"stream": "turnstile-east", "weight": 4.2, "window_offsets": [10, 10, 15], "base_value": 36.0, "spread": 1.8, "drift": 0.8, "hotspot_offsets": [10], "hotspot_bonus": 14.0},
                {"stream": "camera-lobby", "weight": 1.5, "window_offsets": [15, 15, 20], "base_value": 30.5, "spread": 1.5, "drift": 0.5, "hotspot_offsets": [15], "hotspot_bonus": 6.5},
                {"stream": "hvac-north", "weight": 1.0, "window_offsets": [0, 10, 20], "base_value": 24.8, "spread": 1.0, "drift": 0.2},
                {"stream": "badge-reader", "weight": 0.8, "window_offsets": [5, 20], "base_value": 26.4, "spread": 1.1, "drift": 0.3},
            ],
        },
        "live-ops": {
            "balanced": [
                {"stream": "ingest-primary", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 42.0, "spread": 1.8, "drift": 0.7},
                {"stream": "chat-presence", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 38.0, "spread": 1.6, "drift": 0.5},
                {"stream": "moderation-queue", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 35.5, "spread": 1.4, "drift": 0.4},
                {"stream": "reaction-fanout", "weight": 1.0, "window_offsets": [0, 5, 10, 15], "base_value": 39.0, "spread": 1.7, "drift": 0.6},
            ],
            "skewed": [
                {"stream": "moderation-queue", "weight": 3.9, "window_offsets": [20, 20, 25], "base_value": 49.0, "spread": 2.1, "drift": 0.9, "hotspot_offsets": [20], "hotspot_bonus": 11.0},
                {"stream": "reaction-fanout", "weight": 1.6, "window_offsets": [15, 15, 20], "base_value": 43.0, "spread": 1.8, "drift": 0.7, "hotspot_offsets": [15], "hotspot_bonus": 5.5},
                {"stream": "ingest-primary", "weight": 1.0, "window_offsets": [0, 10, 20], "base_value": 41.5, "spread": 1.7, "drift": 0.5},
                {"stream": "chat-presence", "weight": 0.9, "window_offsets": [5, 10, 25], "base_value": 37.6, "spread": 1.4, "drift": 0.4},
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
                hotspot_offsets=profile.get("hotspot_offsets"),
                hotspot_bonus=profile.get("hotspot_bonus", 0.0),
            )
        )
    lines.sort(key=lambda line: line.split(",", maxsplit=2)[1])
    return lines[:records]
```

### Benchmark note hook: `plugins_streaming_window.benchmark_notes`

- Summary: Describe the intended hot windows and portfolio story for each family.
- Source line: `215`
- Source anchor: `plugins_streaming_window.py#L215-L284`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_streaming_window.py#L215-L284>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended hot windows and portfolio story for each family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Even telemetry cadence",
                "detail": "The default balanced family spreads sensor updates across multiple windows and streams, so reducer load should stay close while still demonstrating time-bucket aggregation.",
                "severity": "info",
                "takeaway": "Use this as the calm baseline before introducing a window hotspot that is caused by workload shape rather than partitioning noise.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Sensor alpha window spike",
                "detail": "`sensor-alpha@2026-04-17T09:05:00Z` is intentionally overweighted, so the hottest reducer should look like one telemetry stream concentrating most of its work into a single five-minute bucket.",
                "severity": "watch",
                "hotspot_keys": ["sensor-alpha@2026-04-17T09:05:00Z"],
                "takeaway": "This is the simplest windowing story for explaining why time buckets can become hotspots even when the upstream stream names look balanced overall.",
            },
        ],
        ("balanced", "iot-burst"): [
            {
                "title": "Staggered building telemetry",
                "detail": "The balanced IoT family rotates turnstiles, cameras, HVAC, and badge readers across adjacent windows so the output reads like a healthy campus-building control loop.",
                "severity": "info",
                "takeaway": "Good for showing the plugin as a normal ops dashboard baseline before a rush-hour burst distorts one window.",
            },
        ],
        ("skewed", "iot-burst"): [
            {
                "title": "Turnstile rush-hour burst",
                "detail": "`turnstile-east@2026-04-17T09:10:00Z` dominates this family with both heavier volume and elevated values, so the hottest reducer should read like a lobby ingress spike during class changeover.",
                "severity": "risk",
                "hotspot_keys": ["turnstile-east@2026-04-17T09:10:00Z"],
                "takeaway": "This turns the plugin into a windowed-streaming case study about burst concentration, not just generic per-key aggregation.",
            },
            {
                "title": "Lobby camera spillover",
                "detail": "`camera-lobby@2026-04-17T09:15:00Z` forms a second-tier hotspot right behind the turnstile window, which helps the benchmark tell a fuller story about adjacent systems reacting to the same surge.",
                "severity": "watch",
                "hotspot_keys": ["camera-lobby@2026-04-17T09:15:00Z"],
                "takeaway": "Keep this note when you want the report to show cross-stream spillover instead of only the single biggest bucket.",
            },
        ],
        ("balanced", "live-ops"): [
            {
                "title": "Steady live-ops baseline",
                "detail": "The balanced live-ops family keeps ingest, presence, moderation, and fanout windows close enough that the report reads like a normal event stream instead of a launch incident.",
                "severity": "info",
                "takeaway": "Use this as the before state for the live moderation surge story.",
            },
        ],
        ("skewed", "live-ops"): [
            {
                "title": "Moderation queue pile-up",
                "detail": "`moderation-queue@2026-04-17T09:20:00Z` becomes the obvious hotspot here, so the window summary looks like one burst of chat events overwhelming moderation capacity during a live launch.",
                "severity": "risk",
                "hotspot_keys": ["moderation-queue@2026-04-17T09:20:00Z"],
                "takeaway": "This family is useful when you want a streaming-systems narrative about time-bucket pressure rather than user sessions or service latency.",
            },
            {
                "title": "Reaction fanout echo",
                "detail": "`reaction-fanout@2026-04-17T09:15:00Z` is the supporting hotspot behind moderation, which helps explain how bursty audience behavior can surface in multiple downstream windows.",
                "severity": "watch",
                "hotspot_keys": ["reaction-fanout@2026-04-17T09:15:00Z"],
                "takeaway": "Keep this annotation when you want the benchmark to tell a richer multi-stage streaming pipeline story.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```

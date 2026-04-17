# Mini MapReduce plugin doc: `plugin-rolling-window-join`

## Snapshot

- Plugin path: `projects/mini-mapreduce-lab/plugins_rolling_window_join.py`
- Summary: Rolling-window join plugin for multi-stream correlation and pipeline-debug demos.
- Dataset families: `default, checkout-funnel, incident-correlation`
- Catalog badges: `5 hooks` · `3 dataset families` · `commit pinned` · `github linked`
- Repository commit: `2332425c37ad2eb7d0399cb11e91a2354e189d22`
- Catalog index: [plugin catalog](../plugin-catalog.md)
- Alternate format: [HTML](plugin-rolling-window-join.html)

## Hook summary

| Hook | Export | Signature | Details | Source |
| --- | --- | --- | --- | --- |
| Mapper | `plugins_rolling_window_join.map_records` | `map_records(lines)` | Emit per-correlation-key event batches from key,side,timestamp,label rows.<br>line 182<br>anchor `plugins_rolling_window_join.py#L182-L196` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196) |
| Reducer | `plugins_rolling_window_join.reduce_key` | `reduce_key(key, values)` | Pair left/right events within a rolling join window and summarize unmatched spillover.<br>line 204<br>anchor `plugins_rolling_window_join.py#L204-L270` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270) |
| Combiner | `plugins_rolling_window_join.combine_values` | `combine_values(_key, values)` | Keep shard-local join candidates JSON-safe before final pairing.<br>line 199<br>anchor `plugins_rolling_window_join.py#L199-L201` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201) |
| Benchmark generator | `plugins_rolling_window_join.benchmark_records` | `benchmark_records(scenario, records, seed, dataset_family='default')` | Generate deterministic two-stream correlation fixtures for rolling join demos.<br>line 273<br>anchor `plugins_rolling_window_join.py#L273-L348` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348) |
| Benchmark note hook | `plugins_rolling_window_join.benchmark_notes` | `benchmark_notes(scenario, dataset_family='default')` | Describe the intended join hotspot and portfolio story for each synthetic family.<br>line 351<br>anchor `plugins_rolling_window_join.py#L351-L420` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420) |

## Hook source excerpts

### Mapper: `plugins_rolling_window_join.map_records`

- Summary: Emit per-correlation-key event batches from key,side,timestamp,label rows.
- Source line: `182`
- Source anchor: `plugins_rolling_window_join.py#L182-L196`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L182-L196>

```python
def map_records(lines):
    """Emit per-correlation-key event batches from key,side,timestamp,label rows."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        key, side, event_at, label = [part.strip() for part in stripped.split(",", maxsplit=3)]
        normalized_side = side.lower()
        if normalized_side not in {"left", "right"}:
            raise ValueError("rolling-window-join side must be 'left' or 'right'")
        yield key.lower(), {
            "side": normalized_side,
            "event_at": _isoformat_z(_parse_timestamp(event_at)),
            "label": label,
        }
```

### Reducer: `plugins_rolling_window_join.reduce_key`

- Summary: Pair left/right events within a rolling join window and summarize unmatched spillover.
- Source line: `204`
- Source anchor: `plugins_rolling_window_join.py#L204-L270`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L204-L270>

```python
def reduce_key(key, values):
    """Pair left/right events within a rolling join window and summarize unmatched spillover."""
    merged = _merge_event_batches(values)
    events = merged["events"]
    left_events = [event for event in events if event["side"] == "left"]
    right_events = [event for event in events if event["side"] == "right"]
    used_right = set()
    windows = {}
    gap_seconds_values = []

    for left_event in left_events:
        left_time = _parse_timestamp(left_event["event_at"])
        best_index = None
        best_gap = None
        for index, right_event in enumerate(right_events):
            if index in used_right:
                continue
            right_time = _parse_timestamp(right_event["event_at"])
            gap_seconds = abs((right_time - left_time).total_seconds())
            if gap_seconds > JOIN_WINDOW_SECONDS:
                continue
            if best_index is None or gap_seconds < best_gap or (
                gap_seconds == best_gap and right_event["event_at"] < right_events[best_index]["event_at"]
            ):
                best_index = index
                best_gap = gap_seconds
        if best_index is None:
            _record_unmatched(windows, event=left_event, side="left")
            continue
        used_right.add(best_index)
        matched_right = right_events[best_index]
        gap_seconds = float(best_gap if best_gap is not None else 0.0)
        gap_seconds_values.append(gap_seconds)
        _record_matched_pair(windows, left_event=left_event, right_event=matched_right, gap_seconds=gap_seconds)

    for index, right_event in enumerate(right_events):
        if index not in used_right:
            _record_unmatched(windows, event=right_event, side="right")

    finalized_windows = [_finalize_window_summary(windows[window_key]) for window_key in sorted(windows)]
    matched_pairs = sum(item["matched_pairs"] for item in finalized_windows)
    unmatched_left = sum(item["left_only_events"] for item in finalized_windows)
    unmatched_right = sum(item["right_only_events"] for item in finalized_windows)
    total_left = sum(item["left_events"] for item in finalized_windows)
    total_right = sum(item["right_events"] for item in finalized_windows)
    hottest_window = max(
        finalized_windows,
        key=lambda item: (item["matched_pairs"], item["left_events"] + item["right_events"], item["window_start"]),
        default=None,
    )
    matched_candidate_total = min(total_left, total_right)
    return {
        "correlation_key": key,
        "window_count": len(finalized_windows),
        "left_events": total_left,
        "right_events": total_right,
        "matched_pairs": matched_pairs,
        "unmatched_left_events": unmatched_left,
        "unmatched_right_events": unmatched_right,
        "join_coverage_rate": round(matched_pairs / matched_candidate_total, 3) if matched_candidate_total else 0.0,
        "avg_gap_seconds": round(sum(gap_seconds_values) / len(gap_seconds_values), 3) if gap_seconds_values else 0.0,
        "max_gap_seconds": round(max(gap_seconds_values), 3) if gap_seconds_values else 0.0,
        "join_window_minutes": JOIN_WINDOW_MINUTES,
        "hottest_window_start": hottest_window["window_start"] if hottest_window else None,
        "hottest_window_matches": hottest_window["matched_pairs"] if hottest_window else 0,
        "windows": finalized_windows,
    }
```

### Combiner: `plugins_rolling_window_join.combine_values`

- Summary: Keep shard-local join candidates JSON-safe before final pairing.
- Source line: `199`
- Source anchor: `plugins_rolling_window_join.py#L199-L201`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L199-L201>

```python
def combine_values(_key, values):
    """Keep shard-local join candidates JSON-safe before final pairing."""
    return {"events": sorted(values, key=lambda event: (event["event_at"], event["side"], event["label"]))}
```

### Benchmark generator: `plugins_rolling_window_join.benchmark_records`

- Summary: Generate deterministic two-stream correlation fixtures for rolling join demos.
- Source line: `273`
- Source anchor: `plugins_rolling_window_join.py#L273-L348`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L273-L348>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic two-stream correlation fixtures for rolling join demos."""
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    base_time = datetime(2026, 4, 17, 9, 0, tzinfo=timezone.utc)

    families = {
        "default": {
            "balanced": [
                {"key": "join-pod-alpha", "weight": 1.0, "window_offsets": [0, 5, 10], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.86, "right_lag_seconds": 52},
                {"key": "join-pod-beta", "weight": 1.0, "window_offsets": [0, 5, 10], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.84, "right_lag_seconds": 61},
                {"key": "join-pod-gamma", "weight": 1.0, "window_offsets": [5, 10, 15], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.83, "right_lag_seconds": 57},
                {"key": "join-pod-delta", "weight": 1.0, "window_offsets": [0, 10, 15], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.82, "right_lag_seconds": 68},
            ],
            "skewed": [
                {"key": "join-hotspot", "weight": 4.0, "window_offsets": [10, 10, 15], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.72, "right_lag_seconds": 97, "hotspot_offsets": [10], "hotspot_bonus": 40, "left_only_share": 0.7},
                {"key": "join-pod-beta", "weight": 1.1, "window_offsets": [0, 10, 15], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.82, "right_lag_seconds": 64},
                {"key": "join-pod-gamma", "weight": 1.0, "window_offsets": [5, 15, 20], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.8, "right_lag_seconds": 70},
                {"key": "join-pod-delta", "weight": 0.9, "window_offsets": [0, 15, 20], "left_label": "request-start", "right_label": "request-finish", "match_ratio": 0.78, "right_lag_seconds": 75},
            ],
        },
        "checkout-funnel": {
            "balanced": [
                {"key": "checkout-core", "weight": 1.2, "window_offsets": [5, 10, 15], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.88, "right_lag_seconds": 48},
                {"key": "express-lane", "weight": 1.0, "window_offsets": [5, 10, 15], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.9, "right_lag_seconds": 38},
                {"key": "promo-retry", "weight": 1.0, "window_offsets": [0, 10, 20], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.8, "right_lag_seconds": 66},
                {"key": "inventory-sync", "weight": 0.9, "window_offsets": [0, 5, 15], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.84, "right_lag_seconds": 58},
            ],
            "skewed": [
                {"key": "checkout-core", "weight": 4.3, "window_offsets": [10, 10, 15], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.7, "right_lag_seconds": 102, "hotspot_offsets": [10], "hotspot_bonus": 55, "left_only_share": 0.75},
                {"key": "promo-retry", "weight": 1.5, "window_offsets": [10, 15, 20], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.76, "right_lag_seconds": 88, "hotspot_offsets": [15], "hotspot_bonus": 32, "left_only_share": 0.65},
                {"key": "express-lane", "weight": 1.0, "window_offsets": [5, 15, 20], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.86, "right_lag_seconds": 42},
                {"key": "inventory-sync", "weight": 0.8, "window_offsets": [0, 10, 20], "left_label": "cart-update", "right_label": "payment-auth", "match_ratio": 0.8, "right_lag_seconds": 63},
            ],
        },
        "incident-correlation": {
            "balanced": [
                {"key": "payments-api", "weight": 1.1, "window_offsets": [0, 5, 10], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.83, "right_lag_seconds": 74},
                {"key": "auth-gateway", "weight": 1.0, "window_offsets": [0, 10, 15], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.82, "right_lag_seconds": 81},
                {"key": "search-api", "weight": 1.0, "window_offsets": [5, 10, 20], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.84, "right_lag_seconds": 72},
                {"key": "edge-cache", "weight": 0.9, "window_offsets": [0, 15, 20], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.8, "right_lag_seconds": 90},
            ],
            "skewed": [
                {"key": "payments-api", "weight": 4.1, "window_offsets": [15, 20, 20], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.68, "right_lag_seconds": 118, "hotspot_offsets": [20], "hotspot_bonus": 48, "left_only_share": 0.72},
                {"key": "auth-gateway", "weight": 1.4, "window_offsets": [10, 15, 20], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.74, "right_lag_seconds": 96, "hotspot_offsets": [15], "hotspot_bonus": 26, "left_only_share": 0.62},
                {"key": "search-api", "weight": 1.0, "window_offsets": [5, 15, 25], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.82, "right_lag_seconds": 77},
                {"key": "edge-cache", "weight": 0.8, "window_offsets": [0, 10, 25], "left_label": "alert-fired", "right_label": "deploy-event", "match_ratio": 0.78, "right_lag_seconds": 88},
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
            _generate_join_events(
                key=profile["key"],
                count=count,
                base_time=base_time,
                window_offsets=profile["window_offsets"],
                left_label=profile["left_label"],
                right_label=profile["right_label"],
                rng=rng,
                match_ratio=profile["match_ratio"],
                right_lag_seconds=profile["right_lag_seconds"],
                hotspot_offsets=profile.get("hotspot_offsets"),
                hotspot_bonus=profile.get("hotspot_bonus", 0),
                left_only_share=profile.get("left_only_share", 0.5),
            )
        )
    lines.sort(key=lambda line: tuple(line.split(",", maxsplit=3)[:3]))
    return lines[:records]
```

### Benchmark note hook: `plugins_rolling_window_join.benchmark_notes`

- Summary: Describe the intended join hotspot and portfolio story for each synthetic family.
- Source line: `351`
- Source anchor: `plugins_rolling_window_join.py#L351-L420`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2332425c37ad2eb7d0399cb11e91a2354e189d22/projects/mini-mapreduce-lab/plugins_rolling_window_join.py#L351-L420>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended join hotspot and portfolio story for each synthetic family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Steady correlation baseline",
                "detail": "The default balanced family keeps four correlation keys close together with only mild spillover, so the report reads like a healthy request/response join workload instead of an incident.",
                "severity": "info",
                "takeaway": "Use this as the before state when explaining how one correlation key can dominate a rolling join workload even if the reducer partitioner stays deterministic.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Join hotspot concentration",
                "detail": "`join-hotspot` absorbs most of the left/right traffic here, so the hottest reducer should read like one correlation key monopolizing the join stage and leaving extra unmatched left events behind.",
                "severity": "watch",
                "hotspot_keys": ["join-hotspot"],
                "takeaway": "This is the simplest story for showing why stream joins introduce both hotspot pressure and mismatch cleanup work.",
            },
        ],
        ("balanced", "checkout-funnel"): [
            {
                "title": "Healthy checkout handoff",
                "detail": "The balanced checkout family keeps `cart-update` and `payment-auth` events closely paired across several flows, so the join output reads like a normal purchase funnel rather than a broken queue.",
                "severity": "info",
                "takeaway": "Good for presenting the plugin as a product/commerce analytics example instead of only infra telemetry.",
            },
        ],
        ("skewed", "checkout-funnel"): [
            {
                "title": "Checkout core backlog",
                "detail": "`checkout-core` becomes the dominant join key with the worst pairing lag, so the report looks like a spike of cart updates outrunning payment authorizations during a launch or sale.",
                "severity": "risk",
                "hotspot_keys": ["checkout-core"],
                "takeaway": "Call out the combination of lower coverage and higher gap when telling the story of queue lag or degraded downstream auth capacity.",
            },
            {
                "title": "Promo retry spillover",
                "detail": "`promo-retry` is the second-tier correlation hotspot behind checkout-core, which helps explain how retries can spread join pressure to a supporting flow instead of one isolated key.",
                "severity": "watch",
                "hotspot_keys": ["promo-retry"],
                "takeaway": "Keep this note when you want the benchmark to feel like a fuller checkout system instead of one synthetic broken key.",
            },
        ],
        ("balanced", "incident-correlation"): [
            {
                "title": "Routine alert/deploy audit trail",
                "detail": "The balanced incident-correlation family keeps alerts and deploy events close enough that the join output reads like a calm incident-review dashboard instead of a chaotic release.",
                "severity": "info",
                "takeaway": "Use this as the steady baseline before a noisy release or rollback starts separating alerts from the deploys that explain them.",
            },
        ],
        ("skewed", "incident-correlation"): [
            {
                "title": "Payments incident war room",
                "detail": "`payments-api` dominates the skewed incident family with long join gaps and extra unmatched alerts, so the benchmark looks like a release that triggered alarms faster than deploy metadata propagated.",
                "severity": "risk",
                "hotspot_keys": ["payments-api"],
                "takeaway": "This turns the plugin into a systems-debugging narrative about correlating alerts, deploys, and lagging metadata streams.",
            },
            {
                "title": "Auth gateway follow-on noise",
                "detail": "`auth-gateway` forms a smaller supporting hotspot that helps the report tell a more realistic multi-service release story instead of one isolated outage key.",
                "severity": "watch",
                "hotspot_keys": ["auth-gateway"],
                "takeaway": "Keep this note when you want to explain correlated release fallout across adjacent services.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```

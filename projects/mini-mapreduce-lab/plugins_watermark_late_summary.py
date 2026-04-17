"""Watermark-aware late-event summary plugin for out-of-order stream-processing demos."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

JOB_NAME = "plugin-watermark-late-summary"
BENCHMARK_DATASET_FAMILIES = ["default", "sensor-backfill", "live-replay"]
WINDOW_MINUTES = 5
WATERMARK_DELAY_MINUTES = 4
ALLOWED_LATENESS_MINUTES = 3


def _parse_timestamp(value):
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _isoformat_z(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _window_start(value):
    floored_minute = value.minute - (value.minute % WINDOW_MINUTES)
    return value.replace(minute=floored_minute, second=0, microsecond=0)


def _watermark_for(max_seen_event_time):
    if max_seen_event_time is None:
        return None
    return max_seen_event_time - timedelta(minutes=WATERMARK_DELAY_MINUTES)


def _merge_event_batches(values):
    events = []
    for item in values:
        events.extend(item["events"])
    events.sort(key=lambda event: (event["arrived_at"], event["event_at"], event["value"]))
    return {"events": events}


def _new_window_summary(window_start):
    window_end = window_start + timedelta(minutes=WINDOW_MINUTES)
    window_close_at = window_end + timedelta(minutes=ALLOWED_LATENESS_MINUTES)
    return {
        "window_start": _isoformat_z(window_start),
        "window_end": _isoformat_z(window_end),
        "window_close_at": _isoformat_z(window_close_at),
        "events_seen": 0,
        "accepted_events": 0,
        "on_time_events": 0,
        "late_accepted_events": 0,
        "dropped_late_events": 0,
        "sum_value": 0.0,
        "min_value": None,
        "max_value": None,
        "first_event_at": None,
        "last_event_at": None,
        "first_arrival_at": None,
        "last_arrival_at": None,
    }


def _update_window_summary(summary, *, event_at, arrived_at, value, late, dropped):
    event_at_iso = _isoformat_z(event_at)
    arrived_at_iso = _isoformat_z(arrived_at)
    summary["events_seen"] += 1
    if summary["first_arrival_at"] is None or arrived_at_iso < summary["first_arrival_at"]:
        summary["first_arrival_at"] = arrived_at_iso
    if summary["last_arrival_at"] is None or arrived_at_iso > summary["last_arrival_at"]:
        summary["last_arrival_at"] = arrived_at_iso

    if dropped:
        summary["dropped_late_events"] += 1
        return

    summary["accepted_events"] += 1
    if late:
        summary["late_accepted_events"] += 1
    else:
        summary["on_time_events"] += 1
    summary["sum_value"] = round(summary["sum_value"] + float(value), 3)
    summary["min_value"] = float(value) if summary["min_value"] is None else min(summary["min_value"], float(value))
    summary["max_value"] = float(value) if summary["max_value"] is None else max(summary["max_value"], float(value))
    if summary["first_event_at"] is None or event_at_iso < summary["first_event_at"]:
        summary["first_event_at"] = event_at_iso
    if summary["last_event_at"] is None or event_at_iso > summary["last_event_at"]:
        summary["last_event_at"] = event_at_iso


def _finalize_window_summary(summary):
    accepted = int(summary["accepted_events"])
    events_seen = int(summary["events_seen"])
    late_accepted = int(summary["late_accepted_events"])
    dropped = int(summary["dropped_late_events"])
    return {
        "window_start": summary["window_start"],
        "window_end": summary["window_end"],
        "window_close_at": summary["window_close_at"],
        "events_seen": events_seen,
        "accepted_events": accepted,
        "on_time_events": int(summary["on_time_events"]),
        "late_accepted_events": late_accepted,
        "dropped_late_events": dropped,
        "avg_value": round(float(summary["sum_value"]) / accepted, 3) if accepted else 0.0,
        "min_value": round(float(summary["min_value"]), 3) if summary["min_value"] is not None else 0.0,
        "max_value": round(float(summary["max_value"]), 3) if summary["max_value"] is not None else 0.0,
        "late_event_rate": round((late_accepted + dropped) / events_seen, 3) if events_seen else 0.0,
        "first_event_at": summary["first_event_at"],
        "last_event_at": summary["last_event_at"],
        "first_arrival_at": summary["first_arrival_at"],
        "last_arrival_at": summary["last_arrival_at"],
    }


def _allocate_counts(records, weights):
    total_weight = sum(weights)
    allocations = [max(1, int(records * weight / total_weight)) for weight in weights]
    while sum(allocations) > records:
        index = max(range(len(allocations)), key=lambda item: allocations[item])
        if allocations[index] > 1:
            allocations[index] -= 1
        else:
            break
    while sum(allocations) < records:
        index = min(range(len(allocations)), key=lambda item: allocations[item])
        allocations[index] += 1
    return allocations


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


def combine_values(_key, values):
    """Keep shard-local stream event batches JSON-safe before watermark evaluation."""
    return {"events": sorted(values, key=lambda event: (event["arrived_at"], event["event_at"], event["value"]))}


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


def _generate_stream_events(
    *,
    stream,
    count,
    base_time,
    window_offsets,
    base_value,
    spread,
    drift,
    rng,
    late_window_offsets=None,
    drop_window_offsets=None,
    hotspot_window_offsets=None,
    hotspot_bonus=0.0,
):
    lines = []
    for index in range(count):
        cycle = index // len(window_offsets)
        offset = window_offsets[index % len(window_offsets)]
        event_at = base_time + timedelta(minutes=offset + (cycle * 15) + (index % 3))
        delay_minutes = 1 + (index % 2)
        if late_window_offsets and offset in late_window_offsets and index % 4 in (1, 2):
            delay_minutes = 8 + (index % 3)
        if drop_window_offsets and offset in drop_window_offsets and index % 5 == 0:
            delay_minutes = 14 + (index % 3)
        arrived_at = event_at + timedelta(minutes=delay_minutes)

        value = base_value + (cycle * drift) + ((index % 5) - 2) * spread * 0.4 + rng.uniform(-0.35, 0.35)
        if hotspot_window_offsets and offset in hotspot_window_offsets:
            value += hotspot_bonus
        lines.append(
            {
                "arrived_at": _isoformat_z(arrived_at),
                "line": f"{stream},{_isoformat_z(event_at)},{_isoformat_z(arrived_at)},{round(value, 3)}",
            }
        )
    lines.sort(key=lambda item: (item["arrived_at"], item["line"]))
    return [item["line"] for item in lines]


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

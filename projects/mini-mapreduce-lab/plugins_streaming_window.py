"""Streaming-window aggregation plugin for telemetry-style benchmark demos."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

JOB_NAME = "plugin-streaming-window"
BENCHMARK_DATASET_FAMILIES = ["default", "iot-burst", "live-ops"]
WINDOW_MINUTES = 5


def _parse_timestamp(value):
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _isoformat_z(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _window_start(value, window_minutes=WINDOW_MINUTES):
    floored_minute = value.minute - (value.minute % window_minutes)
    return value.replace(minute=floored_minute, second=0, microsecond=0)


def _split_window_key(key):
    stream, window_start = key.rsplit("@", maxsplit=1)
    return stream, window_start


def _merge_window_values(values):
    if not values:
        return {
            "count": 0,
            "sum": 0.0,
            "min": 0.0,
            "max": 0.0,
            "first_event_at": None,
            "last_event_at": None,
        }
    first_event_at = min(item["first_event_at"] for item in values if item["first_event_at"] is not None)
    last_event_at = max(item["last_event_at"] for item in values if item["last_event_at"] is not None)
    return {
        "count": sum(int(item["count"]) for item in values),
        "sum": round(sum(float(item["sum"]) for item in values), 3),
        "min": round(min(float(item["min"]) for item in values), 3),
        "max": round(max(float(item["max"]) for item in values), 3),
        "first_event_at": first_event_at,
        "last_event_at": last_event_at,
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


def combine_values(_key, values):
    """Merge shard-local window summaries before the final reduce step."""
    return _merge_window_values(values)


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


def _generate_stream_events(*, stream, count, base_time, window_offsets, base_value, spread, drift, rng, hotspot_offsets=None, hotspot_bonus=0.0):
    hotspot_offsets = set(hotspot_offsets or [])
    lines = []
    for index in range(count):
        window_offset = window_offsets[index % len(window_offsets)]
        event_time = base_time + timedelta(minutes=window_offset, seconds=((index * 37) + rng.randint(0, 19)) % 290)
        value = base_value + (index % 4) * drift + rng.uniform(-spread, spread)
        if window_offset in hotspot_offsets:
            value += hotspot_bonus
        lines.append(f"{stream},{_isoformat_z(event_time)},{round(value, 3)}")
    return lines


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

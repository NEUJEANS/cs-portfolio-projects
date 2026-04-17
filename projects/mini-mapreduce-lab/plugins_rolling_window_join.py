"""Rolling-window join plugin for multi-stream correlation and pipeline-debug demos."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

JOB_NAME = "plugin-rolling-window-join"
BENCHMARK_DATASET_FAMILIES = ["default", "checkout-funnel", "incident-correlation"]
WINDOW_MINUTES = 5
JOIN_WINDOW_MINUTES = 3
JOIN_WINDOW_SECONDS = JOIN_WINDOW_MINUTES * 60


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


def _window_key(value):
    return _isoformat_z(_window_start(value))


def _window_end_from_key(window_key):
    return _isoformat_z(_parse_timestamp(window_key) + timedelta(minutes=WINDOW_MINUTES))


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


def _merge_event_batches(values):
    events = []
    for item in values:
        events.extend(item["events"])
    events.sort(key=lambda event: (event["event_at"], event["side"], event["label"]))
    return {"events": events}


def _new_window_summary(window_key):
    return {
        "window_start": window_key,
        "window_end": _window_end_from_key(window_key),
        "left_events": 0,
        "right_events": 0,
        "matched_pairs": 0,
        "left_only_events": 0,
        "right_only_events": 0,
        "gap_seconds_total": 0.0,
        "max_gap_seconds": 0.0,
        "sample_pair": None,
    }


def _ensure_window(windows, window_key):
    return windows.setdefault(window_key, _new_window_summary(window_key))


def _record_matched_pair(windows, *, left_event, right_event, gap_seconds):
    window_key = _window_key(min(_parse_timestamp(left_event["event_at"]), _parse_timestamp(right_event["event_at"])))
    summary = _ensure_window(windows, window_key)
    summary["left_events"] += 1
    summary["right_events"] += 1
    summary["matched_pairs"] += 1
    summary["gap_seconds_total"] = round(summary["gap_seconds_total"] + gap_seconds, 3)
    summary["max_gap_seconds"] = round(max(summary["max_gap_seconds"], gap_seconds), 3)
    if summary["sample_pair"] is None:
        summary["sample_pair"] = {
            "left_label": left_event["label"],
            "right_label": right_event["label"],
            "left_event_at": left_event["event_at"],
            "right_event_at": right_event["event_at"],
            "gap_seconds": round(gap_seconds, 3),
        }


def _record_unmatched(windows, *, event, side):
    window_key = _window_key(_parse_timestamp(event["event_at"]))
    summary = _ensure_window(windows, window_key)
    summary[f"{side}_events"] += 1
    summary[f"{side}_only_events"] += 1


def _finalize_window_summary(summary):
    matched_pairs = int(summary["matched_pairs"])
    return {
        "window_start": summary["window_start"],
        "window_end": summary["window_end"],
        "left_events": int(summary["left_events"]),
        "right_events": int(summary["right_events"]),
        "matched_pairs": matched_pairs,
        "left_only_events": int(summary["left_only_events"]),
        "right_only_events": int(summary["right_only_events"]),
        "avg_gap_seconds": round(summary["gap_seconds_total"] / matched_pairs, 3) if matched_pairs else 0.0,
        "max_gap_seconds": round(summary["max_gap_seconds"], 3),
        "sample_pair": summary["sample_pair"],
    }


def _generate_join_events(
    *,
    key,
    count,
    base_time,
    window_offsets,
    left_label,
    right_label,
    rng,
    match_ratio,
    right_lag_seconds,
    hotspot_offsets=None,
    hotspot_bonus=0,
    left_only_share=0.5,
):
    hotspot_offsets = set(hotspot_offsets or [])
    match_pairs = max(1, int((count * match_ratio) // 2)) if count >= 2 else 0
    remaining = max(0, count - (match_pairs * 2))
    left_only_count = min(remaining, max(0, int(round(remaining * left_only_share))))
    right_only_count = remaining - left_only_count

    lines = []
    for index in range(match_pairs):
        offset = window_offsets[index % len(window_offsets)]
        cycle = index // len(window_offsets)
        base_offset_minutes = offset + (cycle * 15)
        base_seconds = ((index * 41) + rng.randint(0, 18)) % 240
        if offset in hotspot_offsets:
            base_seconds = (base_seconds + hotspot_bonus) % 240
        left_event_at = base_time + timedelta(minutes=base_offset_minutes, seconds=base_seconds)
        gap_seconds = max(18, right_lag_seconds + ((index % 5) - 2) * 12 + rng.randint(-6, 6))
        gap_seconds = min(gap_seconds, JOIN_WINDOW_SECONDS - 15)
        right_event_at = left_event_at + timedelta(seconds=gap_seconds)
        lines.append(f"{key},left,{_isoformat_z(left_event_at)},{left_label}")
        lines.append(f"{key},right,{_isoformat_z(right_event_at)},{right_label}")

    for index in range(left_only_count):
        offset = window_offsets[(match_pairs + index) % len(window_offsets)]
        cycle = (match_pairs + index) // len(window_offsets)
        event_at = base_time + timedelta(
            minutes=offset + (cycle * 15),
            seconds=((index * 53) + rng.randint(0, 25)) % 240,
        )
        lines.append(f"{key},left,{_isoformat_z(event_at)},{left_label}-pending")

    for index in range(right_only_count):
        offset = window_offsets[(match_pairs + left_only_count + index) % len(window_offsets)]
        cycle = (match_pairs + left_only_count + index) // len(window_offsets)
        event_at = base_time + timedelta(
            minutes=offset + (cycle * 15),
            seconds=((index * 59) + rng.randint(0, 25)) % 240,
        )
        lines.append(f"{key},right,{_isoformat_z(event_at)},{right_label}-orphan")

    lines.sort(key=lambda line: tuple(line.split(",", maxsplit=3)[:3]))
    return lines[:count]


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


def combine_values(_key, values):
    """Keep shard-local join candidates JSON-safe before final pairing."""
    return {"events": sorted(values, key=lambda event: (event["event_at"], event["side"], event["label"]))}


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

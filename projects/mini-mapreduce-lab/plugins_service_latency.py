"""Service-latency summary plugin for observability-style benchmark demos."""

from __future__ import annotations

import math
import random

JOB_NAME = "plugin-service-latency"
BENCHMARK_DATASET_FAMILIES = ["default", "incident-spike", "batch-window"]


def _merge_latency_values(values):
    count = sum(int(item["count"]) for item in values)
    total_ms = sum(float(item["sum_ms"]) for item in values)
    max_ms = max(float(item["max_ms"]) for item in values) if values else 0.0
    samples = [float(sample) for item in values for sample in item["samples_ms"]]
    return {
        "count": count,
        "sum_ms": round(total_ms, 3),
        "max_ms": round(max_ms, 3),
        "samples_ms": samples,
    }


def _nearest_rank_percentile(samples, percentile):
    if not samples:
        return 0.0
    ordered = sorted(float(sample) for sample in samples)
    rank = max(1, math.ceil((percentile / 100) * len(ordered)))
    return round(ordered[rank - 1], 3)


def map_records(lines):
    """Parse comma-separated service/latency rows into partial latency summaries."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        service, latency_ms = stripped.split(",", maxsplit=1)
        latency_value = round(float(latency_ms.strip()), 3)
        yield service.strip().lower(), {
            "count": 1,
            "sum_ms": latency_value,
            "max_ms": latency_value,
            "samples_ms": [latency_value],
        }


def combine_values(_key, values):
    """Merge shard-local latency summaries before the final reduce step."""
    return _merge_latency_values(values)


def reduce_key(_key, values):
    """Return count, average, p95, and max latency for one service key."""
    merged = _merge_latency_values(values)
    count = int(merged["count"])
    average = round(float(merged["sum_ms"]) / count, 3) if count else 0.0
    return {
        "count": count,
        "avg_ms": average,
        "p95_ms": _nearest_rank_percentile(merged["samples_ms"], 95),
        "max_ms": round(float(merged["max_ms"]), 3),
    }


def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic latency fixtures for multiple observability-style families."""
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)

    families = {
        "default": {
            "balanced": [
                ("edge-api", 82, 9),
                ("catalog-api", 76, 8),
                ("checkout-api", 88, 10),
                ("search-api", 71, 7),
            ],
            "skewed": [
                ("edge-api", 144, 26),
                ("catalog-api", 84, 10),
                ("checkout-api", 96, 12),
                ("search-api", 74, 8),
            ],
        },
        "incident-spike": {
            "balanced": [
                ("auth-gateway", 118, 12),
                ("session-cache", 89, 8),
                ("token-service", 102, 10),
                ("profile-read", 78, 7),
            ],
            "skewed": [
                ("auth-gateway", 236, 54),
                ("session-cache", 148, 22),
                ("token-service", 121, 14),
                ("profile-read", 83, 9),
            ],
        },
        "batch-window": {
            "balanced": [
                ("warehouse-loader", 264, 30),
                ("index-builder", 221, 24),
                ("backfill-runner", 246, 27),
                ("metrics-rollup", 198, 21),
            ],
            "skewed": [
                ("warehouse-loader", 462, 86),
                ("index-builder", 274, 34),
                ("backfill-runner", 318, 42),
                ("metrics-rollup", 206, 25),
            ],
        },
    }
    if dataset_family not in families or scenario not in families[dataset_family]:
        raise ValueError(f"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}")

    templates = families[dataset_family][scenario]
    lines = []
    for index in range(records):
        service, base_ms, spread_ms = templates[index % len(templates)]
        jitter = rng.randint(-spread_ms, spread_ms)
        lines.append(f"{service},{round(base_ms + jitter, 3)}")
    if scenario == "skewed":
        hotspot = templates[0][0]
        for index in range(max(1, records // 3)):
            latency = templates[0][1] + templates[0][2] + rng.randint(18, 52)
            lines[index] = f"{hotspot},{round(latency, 3)}"
    return lines


def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended hot services for each synthetic latency family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Healthy service spread",
                "detail": "The default balanced latency family rotates evenly across four APIs, so reducer load should stay close while the output still looks like a small production stack.",
                "severity": "info",
                "takeaway": "Use this as the calm baseline before introducing latency hotspots or on-call incident narratives.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Edge API hotspot",
                "detail": "`edge-api` is intentionally heavier and slower here, so the hottest reducer should read like a front-door latency spike instead of a partitioning accident.",
                "severity": "watch",
                "hotspot_keys": ["edge-api"],
                "takeaway": "This is the simplest observability-style story for discussing why p95 matters more than the mean under hotspot traffic.",
            },
        ],
        ("balanced", "incident-spike"): [
            {
                "title": "Steady auth baseline",
                "detail": "The balanced incident family keeps auth, cache, token, and profile services close enough that the report highlights normal service-to-service variance rather than an outage.",
                "severity": "info",
                "takeaway": "This is the before state for the incident-spike storyline.",
            },
        ],
        ("skewed", "incident-spike"): [
            {
                "title": "Auth gateway timeout storm",
                "detail": "`auth-gateway` dominates this family with elevated latency, so the hottest reducer should look like an outage-era timeout storm concentrated around one service.",
                "severity": "risk",
                "hotspot_keys": ["auth-gateway"],
                "takeaway": "Call out the gap between average and p95 latency here to explain why long-tail spikes matter during incidents.",
            },
            {
                "title": "Session cache spillover",
                "detail": "`session-cache` forms the second-tier hotspot behind the auth gateway, which helps tell a broader bottleneck story about downstream spillover instead of a single bad node.",
                "severity": "watch",
                "hotspot_keys": ["session-cache"],
                "takeaway": "Keep this annotation when you want a fuller causal narrative about cascading latency during the same incident.",
            },
            {
                "title": "Profile path cool lane",
                "detail": "`profile-read` stays comparatively cool, so it works as a low-priority contrast point or a card to collapse in tighter portfolio reports.",
                "severity": "info",
                "hotspot_keys": ["profile-read"],
                "takeaway": "Use annotation filtering when you want the report to focus only on the riskiest paths.",
            },
        ],
        ("balanced", "batch-window"): [
            {
                "title": "Even batch cadence",
                "detail": "The balanced batch-window family rotates evenly across warehouse, indexing, backfill, and metrics jobs so the reducer heatmap reflects a normal overnight data window.",
                "severity": "info",
                "takeaway": "This family is useful when you want a data-engineering story rather than an incident-response story.",
            },
        ],
        ("skewed", "batch-window"): [
            {
                "title": "Warehouse loader saturation",
                "detail": "`warehouse-loader` is intentionally the hottest and slowest key here, so the benchmark looks like a batch-window saturation problem during an oversized ingest run.",
                "severity": "watch",
                "hotspot_keys": ["warehouse-loader"],
                "takeaway": "Use this family to talk about long-running ETL contention and why reducer skew can line up with operational bottlenecks.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])

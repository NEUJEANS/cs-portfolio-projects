# Mini MapReduce plugin doc: `plugin-service-latency`

## Snapshot

- Plugin path: `projects/mini-mapreduce-lab/plugins_service_latency.py`
- Summary: Service-latency summary plugin for observability-style benchmark demos.
- Dataset families: `default, incident-spike, batch-window`
- Catalog badges: `5 hooks` · `3 dataset families` · `commit pinned` · `github linked`
- Repository commit: `c0c005d1bcef0d903008fadbb7bd0f4faa872508`
- Catalog index: [plugin catalog](../plugin-catalog.md)
- Alternate format: [HTML](plugin-service-latency.html)

## Hook summary

| Hook | Export | Signature | Details | Source |
| --- | --- | --- | --- | --- |
| Mapper | `plugins_service_latency.map_records` | `map_records(lines)` | Parse comma-separated service/latency rows into partial latency summaries.<br>line 33<br>anchor `plugins_service_latency.py#L33-L46` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46) |
| Reducer | `plugins_service_latency.reduce_key` | `reduce_key(_key, values)` | Return count, average, p95, and max latency for one service key.<br>line 54<br>anchor `plugins_service_latency.py#L54-L64` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64) |
| Combiner | `plugins_service_latency.combine_values` | `combine_values(_key, values)` | Merge shard-local latency summaries before the final reduce step.<br>line 49<br>anchor `plugins_service_latency.py#L49-L51` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51) |
| Benchmark generator | `plugins_service_latency.benchmark_records` | `benchmark_records(scenario, records, seed, dataset_family='default')` | Generate deterministic latency fixtures for multiple observability-style families.<br>line 67<br>anchor `plugins_service_latency.py#L67-L131` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131) |
| Benchmark note hook | `plugins_service_latency.benchmark_notes` | `benchmark_notes(scenario, dataset_family='default')` | Describe the intended hot services for each synthetic latency family.<br>line 134<br>anchor `plugins_service_latency.py#L134-L203` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203) |

## Hook source excerpts

### Mapper: `plugins_service_latency.map_records`

- Summary: Parse comma-separated service/latency rows into partial latency summaries.
- Source line: `33`
- Source anchor: `plugins_service_latency.py#L33-L46`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46>

```python
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
```

### Reducer: `plugins_service_latency.reduce_key`

- Summary: Return count, average, p95, and max latency for one service key.
- Source line: `54`
- Source anchor: `plugins_service_latency.py#L54-L64`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64>

```python
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
```

### Combiner: `plugins_service_latency.combine_values`

- Summary: Merge shard-local latency summaries before the final reduce step.
- Source line: `49`
- Source anchor: `plugins_service_latency.py#L49-L51`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51>

```python
def combine_values(_key, values):
    """Merge shard-local latency summaries before the final reduce step."""
    return _merge_latency_values(values)
```

### Benchmark generator: `plugins_service_latency.benchmark_records`

- Summary: Generate deterministic latency fixtures for multiple observability-style families.
- Source line: `67`
- Source anchor: `plugins_service_latency.py#L67-L131`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131>

```python
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
```

### Benchmark note hook: `plugins_service_latency.benchmark_notes`

- Summary: Describe the intended hot services for each synthetic latency family.
- Source line: `134`
- Source anchor: `plugins_service_latency.py#L134-L203`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203>

```python
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
```

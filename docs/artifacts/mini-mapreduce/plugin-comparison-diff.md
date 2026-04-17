# Mini MapReduce plugin inspection

- Plugin count: `3`
- Diff count: `2`

## Catalog quick links

- [`plugin-average-score`](#plugin-average-score) — Average-score analytics plugin with synthetic cohort benchmark families. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, exam-cram, project-week`)
- [`plugin-service-latency`](#plugin-service-latency) — Service-latency summary plugin for observability-style benchmark demos. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, incident-spike, batch-window`)
- [`plugin-max-score`](#plugin-max-score) — Maximum-score reducer plugin for simple leaderboard-style demos. (`3 hooks` · `no dataset families` · `commit pinned` · `github linked`; families: `-`)

## Plugin summary

| Name | Plugin | Commit | Summary | Mapper | Reducer | Combiner | Benchmark generator | Benchmark note hook | Dataset families |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `plugin-average-score` | `projects/mini-mapreduce-lab/plugins_average_score.py` | `5d6ac8f8b926` | Average-score analytics plugin with synthetic cohort benchmark families. | `plugins_average_score.map_records`<br><small>`map_records(lines)`<br>line 7<br>plugins_average_score.py#L7-L13<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13)<br>Emit per-student sum/count records from comma-separated score lines.</small> | `plugins_average_score.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 23<br>plugins_average_score.py#L23-L27<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27)<br>Return a rounded average score for one student key.</small> | `plugins_average_score.combine_values`<br><small>`combine_values(_key, values)`<br>line 16<br>plugins_average_score.py#L16-L20<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20)<br>Merge shard-local sum/count objects before the final reduce step.</small> | `plugins_average_score.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 30<br>plugins_average_score.py#L30-L60<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60)<br>Generate deterministic cohort score fixtures for benchmark scenarios.</small> | `plugins_average_score.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 63<br>plugins_average_score.py#L63-L132<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132)<br>Describe the intended hot keys for each synthetic benchmark family.</small> | `default, exam-cram, project-week` |
| `plugin-service-latency` | `projects/mini-mapreduce-lab/plugins_service_latency.py` | `5d6ac8f8b926` | Service-latency summary plugin for observability-style benchmark demos. | `plugins_service_latency.map_records`<br><small>`map_records(lines)`<br>line 33<br>plugins_service_latency.py#L33-L46<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46)<br>Parse comma-separated service/latency rows into partial latency summaries.</small> | `plugins_service_latency.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 54<br>plugins_service_latency.py#L54-L64<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64)<br>Return count, average, p95, and max latency for one service key.</small> | `plugins_service_latency.combine_values`<br><small>`combine_values(_key, values)`<br>line 49<br>plugins_service_latency.py#L49-L51<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51)<br>Merge shard-local latency summaries before the final reduce step.</small> | `plugins_service_latency.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 67<br>plugins_service_latency.py#L67-L131<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131)<br>Generate deterministic latency fixtures for multiple observability-style families.</small> | `plugins_service_latency.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 134<br>plugins_service_latency.py#L134-L203<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203)<br>Describe the intended hot services for each synthetic latency family.</small> | `default, incident-spike, batch-window` |
| `plugin-max-score` | `projects/mini-mapreduce-lab/plugins_top_score.py` | `5d6ac8f8b926` | Maximum-score reducer plugin for simple leaderboard-style demos. | `plugins_top_score.map_records`<br><small>`map_records(lines)`<br>line 6<br>plugins_top_score.py#L6-L13<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13)<br>Parse comma-separated score rows into integer leaderboard updates.</small> | `plugins_top_score.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 21<br>plugins_top_score.py#L21-L23<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23)<br>Return the overall maximum score for one student key.</small> | `plugins_top_score.combine_values`<br><small>`combine_values(_key, values)`<br>line 16<br>plugins_top_score.py#L16-L18<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18)<br>Keep the shard-local maximum score for one student key.</small> | - | - | `-` |

## Hook source excerpts

### <a id="plugin-average-score"></a>`plugin-average-score`

- Repository commit: `5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef`
#### Mapper: `plugins_average_score.map_records`
- Source anchor: `plugins_average_score.py#L7-L13`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13>

```python
def map_records(lines):
    """Emit per-student sum/count records from comma-separated score lines."""
    for line in lines:
        if not line.strip():
            continue
        name, score = line.split(",", 1)
        yield name.strip().lower(), {"sum": float(score), "count": 1}
```

#### Reducer: `plugins_average_score.reduce_key`
- Source anchor: `plugins_average_score.py#L23-L27`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27>

```python
def reduce_key(_key, values):
    """Return a rounded average score for one student key."""
    total = sum(item["sum"] for item in values)
    count = sum(item["count"] for item in values)
    return round(total / count, 3) if count else 0.0
```

#### Combiner: `plugins_average_score.combine_values`
- Source anchor: `plugins_average_score.py#L16-L20`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20>

```python
def combine_values(_key, values):
    """Merge shard-local sum/count objects before the final reduce step."""
    total = sum(item["sum"] for item in values)
    count = sum(item["count"] for item in values)
    return {"sum": total, "count": count}
```

#### Benchmark generator: `plugins_average_score.benchmark_records`
- Source anchor: `plugins_average_score.py#L30-L60`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic cohort score fixtures for benchmark scenarios."""
    import random

    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)

    if dataset_family == "default":
        if scenario == "balanced":
            students = [f"team-{index:02d}" for index in range(12)]
            return [f"{students[index % len(students)]},{72 + ((index * 9) % 19)}" for index in range(records)]
        if scenario == "skewed":
            hot_students = ["capstone-core"] * 16 + [f"rotation-{index}" for index in range(4)] + [f"elective-{index}" for index in range(10)]
            return [f"{rng.choice(hot_students)},{65 + rng.randint(0, 30)}" for _ in range(records)]
    elif dataset_family == "exam-cram":
        if scenario == "balanced":
            cohorts = [f"study-group-{index:02d}" for index in range(10)]
            return [f"{cohorts[index % len(cohorts)]},{78 + ((index * 7) % 15)}" for index in range(records)]
        if scenario == "skewed":
            hot_students = ["midterm-sprint"] * 18 + [f"review-{index}" for index in range(4)] + [f"prep-{index}" for index in range(12)]
            return [f"{rng.choice(hot_students)},{70 + rng.randint(0, 25)}" for _ in range(records)]
    elif dataset_family == "project-week":
        if scenario == "balanced":
            squads = [f"studio-{index:02d}" for index in range(8)]
            return [f"{squads[index % len(squads)]},{74 + ((index * 5) % 21)}" for index in range(records)]
        if scenario == "skewed":
            hot_students = ["demo-day-core"] * 12 + [f"integration-{index}" for index in range(6)] + [f"feature-{index}" for index in range(14)]
            return [f"{rng.choice(hot_students)},{68 + rng.randint(0, 28)}" for _ in range(records)]

    raise ValueError(f"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}")
```

#### Benchmark note hook: `plugins_average_score.benchmark_notes`
- Source anchor: `plugins_average_score.py#L63-L132`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended hot keys for each synthetic benchmark family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Even cohort rotation",
                "detail": "The default balanced cohort rotates evenly across team labels, so average-score aggregation stays spread out and mostly tests framework overhead rather than hot students.",
                "severity": "info",
                "takeaway": "Treat any noticeable reducer imbalance here as partition spread, not as a workload-shaped hotspot.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Capstone leader hotspot",
                "detail": "`capstone-core` is the dominant student key here, so the hottest reducer should look like one heavy project lead soaking up repeated score updates.",
                "severity": "watch",
                "hotspot_keys": ["capstone-core"],
                "takeaway": "Use this scenario to explain how a single standout key can dominate reducer traffic even when the final averages remain correct.",
            },
        ],
        ("balanced", "exam-cram"): [
            {
                "title": "Distributed study groups",
                "detail": "Balanced exam-cram fixtures distribute scores across study groups, which makes them a clean baseline before simulating deadline pressure.",
                "severity": "info",
                "takeaway": "This is the calm comparison point for the cram-week hotspot run.",
            },
        ],
        ("skewed", "exam-cram"): [
            {
                "title": "Cram-week surge",
                "detail": "`midterm-sprint` is intentionally overrepresented, so the report should surface one study cohort as the obvious hotspot during cram-week traffic.",
                "severity": "watch",
                "hotspot_keys": ["midterm-sprint"],
                "takeaway": "The skew should read like deadline-driven traffic, not like a partitioner bug.",
            },
        ],
        ("balanced", "project-week"): [
            {
                "title": "Studio squad baseline",
                "detail": "Balanced project-week fixtures rotate across studio squads so reducer load stays close even though the labels feel more portfolio-realistic than generic teams.",
                "severity": "info",
                "takeaway": "This family keeps the story portfolio-friendly without manufacturing a hotspot.",
            },
        ],
        ("skewed", "project-week"): [
            {
                "title": "Demo-day crunch hotspot",
                "detail": "`demo-day-core` is the main hotspot here, with integration and feature tails behind it, so you can narrate the skew as a deadline-driven project crunch.",
                "severity": "risk",
                "hotspot_keys": ["demo-day-core", "integration-0", "feature-0"],
                "takeaway": "This slice is meant to read like a real project-week bottleneck where one squad absorbs the final demo push.",
            },
            {
                "title": "Integration review backlog",
                "detail": "The `integration-*` keys form a second-tier hotspot behind the demo-day core, which makes a good reviewer note when you want to talk about handoff queues instead of only the primary spike.",
                "severity": "watch",
                "hotspot_keys": ["integration-0", "integration-1", "integration-2"],
                "takeaway": "Keep this card when you want a fuller systems story about follow-on bottlenecks after the main project crunch.",
            },
            {
                "title": "Feature-lane tail",
                "detail": "The `feature-*` keys stay spread out and comparatively cooler, so they are useful as a low-priority reviewer note but often safe to collapse in tighter portfolio reports.",
                "severity": "info",
                "hotspot_keys": ["feature-0", "feature-1"],
                "takeaway": "Use annotation filters or overflow summaries when you want to hide softer follow-up notes and keep the report focused on the highest-risk queues.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```

### <a id="plugin-service-latency"></a>`plugin-service-latency`

- Repository commit: `5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef`
#### Mapper: `plugins_service_latency.map_records`
- Source anchor: `plugins_service_latency.py#L33-L46`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46>

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

#### Reducer: `plugins_service_latency.reduce_key`
- Source anchor: `plugins_service_latency.py#L54-L64`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64>

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

#### Combiner: `plugins_service_latency.combine_values`
- Source anchor: `plugins_service_latency.py#L49-L51`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51>

```python
def combine_values(_key, values):
    """Merge shard-local latency summaries before the final reduce step."""
    return _merge_latency_values(values)
```

#### Benchmark generator: `plugins_service_latency.benchmark_records`
- Source anchor: `plugins_service_latency.py#L67-L131`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131>

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

#### Benchmark note hook: `plugins_service_latency.benchmark_notes`
- Source anchor: `plugins_service_latency.py#L134-L203`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203>

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

### <a id="plugin-max-score"></a>`plugin-max-score`

- Repository commit: `5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef`
#### Mapper: `plugins_top_score.map_records`
- Source anchor: `plugins_top_score.py#L6-L13`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13>

```python
def map_records(lines):
    """Parse comma-separated score rows into integer leaderboard updates."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        name, score = stripped.split(",", maxsplit=1)
        yield name.strip().lower(), int(score.strip())
```

#### Reducer: `plugins_top_score.reduce_key`
- Source anchor: `plugins_top_score.py#L21-L23`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23>

```python
def reduce_key(_key, values):
    """Return the overall maximum score for one student key."""
    return max(values)
```

#### Combiner: `plugins_top_score.combine_values`
- Source anchor: `plugins_top_score.py#L16-L18`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18>

```python
def combine_values(_key, values):
    """Keep the shard-local maximum score for one student key."""
    return max(values)
```


## Adjacent diffs

### Diff 1: `projects/mini-mapreduce-lab/plugins_average_score.py` → `projects/mini-mapreduce-lab/plugins_service_latency.py`
- Changed fields: `available_dataset_families, benchmark_generator, benchmark_generator_doc_summary, benchmark_generator_source_anchor, benchmark_generator_source_commit_url, benchmark_generator_source_excerpt, benchmark_generator_source_line, benchmark_generator_source_url, benchmark_note_hook, benchmark_note_hook_doc_summary, benchmark_note_hook_source_anchor, benchmark_note_hook_source_commit_url, benchmark_note_hook_source_excerpt, benchmark_note_hook_source_line, benchmark_note_hook_source_url, combiner, combiner_doc_summary, combiner_source_anchor, combiner_source_commit_url, combiner_source_excerpt, combiner_source_line, combiner_source_url, mapper, mapper_doc_summary, mapper_source_anchor, mapper_source_commit_url, mapper_source_excerpt, mapper_source_line, mapper_source_url, module_doc_summary, name, plugin, reducer, reducer_doc_summary, reducer_source_anchor, reducer_source_commit_url, reducer_source_excerpt, reducer_source_line, reducer_source_url`

| Field | Previous | Current |
| --- | --- | --- |
| `available_dataset_families` | `["default", "exam-cram", "project-week"]` | `["default", "incident-spike", "batch-window"]` |
| `benchmark_generator` | `"plugins_average_score.benchmark_records"` | `"plugins_service_latency.benchmark_records"` |
| `benchmark_generator_doc_summary` | `"Generate deterministic cohort score fixtures for benchmark scenarios."` | `"Generate deterministic latency fixtures for multiple observability-style families."` |
| `benchmark_generator_source_anchor` | `"plugins_average_score.py#L30-L60"` | `"plugins_service_latency.py#L67-L131"` |
| `benchmark_generator_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131"` |
| `benchmark_generator_source_excerpt` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic cohort score fixtures for benchmark scenarios.\"\"\"\n    import random\n\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n\n    if dataset_family == \"default\":\n        if scenario == \"balanced\":\n            students = [f\"team-{index:02d}\" for index in range(12)]\n            return [f\"{students[index % len(students)]},{72 + ((index * 9) % 19)}\" for index in range(records)]\n        if scenario == \"skewed\":\n            hot_students = [\"capstone-core\"] * 16 + [f\"rotation-{index}\" for index in range(4)] + [f\"elective-{index}\" for index in range(10)]\n            return [f\"{rng.choice(hot_students)},{65 + rng.randint(0, 30)}\" for _ in range(records)]\n    elif dataset_family == \"exam-cram\":\n        if scenario == \"balanced\":\n            cohorts = [f\"study-group-{index:02d}\" for index in range(10)]\n            return [f\"{cohorts[index % len(cohorts)]},{78 + ((index * 7) % 15)}\" for index in range(records)]\n        if scenario == \"skewed\":\n            hot_students = [\"midterm-sprint\"] * 18 + [f\"review-{index}\" for index in range(4)] + [f\"prep-{index}\" for index in range(12)]\n            return [f\"{rng.choice(hot_students)},{70 + rng.randint(0, 25)}\" for _ in range(records)]\n    elif dataset_family == \"project-week\":\n        if scenario == \"balanced\":\n            squads = [f\"studio-{index:02d}\" for index in range(8)]\n            return [f\"{squads[index % len(squads)]},{74 + ((index * 5) % 21)}\" for index in range(records)]\n        if scenario == \"skewed\":\n            hot_students = [\"demo-day-core\"] * 12 + [f\"integration-{index}\" for index in range(6)] + [f\"feature-{index}\" for index in range(14)]\n            return [f\"{rng.choice(hot_students)},{68 + rng.randint(0, 28)}\" for _ in range(records)]\n\n    raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")"` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic latency fixtures for multiple observability-style families.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                (\"edge-api\", 82, 9),\n                (\"catalog-api\", 76, 8),\n                (\"checkout-api\", 88, 10),\n                (\"search-api\", 71, 7),\n            ],\n            \"skewed\": [\n                (\"edge-api\", 144, 26),\n                (\"catalog-api\", 84, 10),\n                (\"checkout-api\", 96, 12),\n                (\"search-api\", 74, 8),\n            ],\n        },\n        \"incident-spike\": {\n            \"balanced\": [\n                (\"auth-gateway\", 118, 12),\n                (\"session-cache\", 89, 8),\n                (\"token-service\", 102, 10),\n                (\"profile-read\", 78, 7),\n            ],\n            \"skewed\": [\n                (\"auth-gateway\", 236, 54),\n                (\"session-cache\", 148, 22),\n                (\"token-service\", 121, 14),\n                (\"profile-read\", 83, 9),\n            ],\n        },\n        \"batch-window\": {\n            \"balanced\": [\n                (\"warehouse-loader\", 264, 30),\n                (\"index-builder\", 221, 24),\n                (\"backfill-runner\", 246, 27),\n                (\"metrics-rollup\", 198, 21),\n            ],\n            \"skewed\": [\n                (\"warehouse-loader\", 462, 86),\n                (\"index-builder\", 274, 34),\n                (\"backfill-runner\", 318, 42),\n                (\"metrics-rollup\", 206, 25),\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    templates = families[dataset_family][scenario]\n    lines = []\n    for index in range(records):\n        service, base_ms, spread_ms = templates[index % len(templates)]\n        jitter = rng.randint(-spread_ms, spread_ms)\n        lines.append(f\"{service},{round(base_ms + jitter, 3)}\")\n    if scenario == \"skewed\":\n        hotspot = templates[0][0]\n        for index in range(max(1, records // 3)):\n            latency = templates[0][1] + templates[0][2] + rng.randint(18, 52)\n            lines[index] = f\"{hotspot},{round(latency, 3)}\"\n    return lines"` |
| `benchmark_generator_source_line` | `30` | `67` |
| `benchmark_generator_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131"` |
| `benchmark_note_hook` | `"plugins_average_score.benchmark_notes"` | `"plugins_service_latency.benchmark_notes"` |
| `benchmark_note_hook_doc_summary` | `"Describe the intended hot keys for each synthetic benchmark family."` | `"Describe the intended hot services for each synthetic latency family."` |
| `benchmark_note_hook_source_anchor` | `"plugins_average_score.py#L63-L132"` | `"plugins_service_latency.py#L134-L203"` |
| `benchmark_note_hook_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203"` |
| `benchmark_note_hook_source_excerpt` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hot keys for each synthetic benchmark family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Even cohort rotation\",\n                \"detail\": \"The default balanced cohort rotates evenly across team labels, so average-score aggregation stays spread out and mostly tests framework overhead rather than hot students.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Treat any noticeable reducer imbalance here as partition spread, not as a workload-shaped hotspot.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Capstone leader hotspot\",\n                \"detail\": \"`capstone-core` is the dominant student key here, so the hottest reducer should look like one heavy project lead soaking up repeated score updates.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"capstone-core\"],\n                \"takeaway\": \"Use this scenario to explain how a single standout key can dominate reducer traffic even when the final averages remain correct.\",\n            },\n        ],\n        (\"balanced\", \"exam-cram\"): [\n            {\n                \"title\": \"Distributed study groups\",\n                \"detail\": \"Balanced exam-cram fixtures distribute scores across study groups, which makes them a clean baseline before simulating deadline pressure.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This is the calm comparison point for the cram-week hotspot run.\",\n            },\n        ],\n        (\"skewed\", \"exam-cram\"): [\n            {\n                \"title\": \"Cram-week surge\",\n                \"detail\": \"`midterm-sprint` is intentionally overrepresented, so the report should surface one study cohort as the obvious hotspot during cram-week traffic.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"midterm-sprint\"],\n                \"takeaway\": \"The skew should read like deadline-driven traffic, not like a partitioner bug.\",\n            },\n        ],\n        (\"balanced\", \"project-week\"): [\n            {\n                \"title\": \"Studio squad baseline\",\n                \"detail\": \"Balanced project-week fixtures rotate across studio squads so reducer load stays close even though the labels feel more portfolio-realistic than generic teams.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This family keeps the story portfolio-friendly without manufacturing a hotspot.\",\n            },\n        ],\n        (\"skewed\", \"project-week\"): [\n            {\n                \"title\": \"Demo-day crunch hotspot\",\n                \"detail\": \"`demo-day-core` is the main hotspot here, with integration and feature tails behind it, so you can narrate the skew as a deadline-driven project crunch.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"demo-day-core\", \"integration-0\", \"feature-0\"],\n                \"takeaway\": \"This slice is meant to read like a real project-week bottleneck where one squad absorbs the final demo push.\",\n            },\n            {\n                \"title\": \"Integration review backlog\",\n                \"detail\": \"The `integration-*` keys form a second-tier hotspot behind the demo-day core, which makes a good reviewer note when you want to talk about handoff queues instead of only the primary spike.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"integration-0\", \"integration-1\", \"integration-2\"],\n                \"takeaway\": \"Keep this card when you want a fuller systems story about follow-on bottlenecks after the main project crunch.\",\n            },\n            {\n                \"title\": \"Feature-lane tail\",\n                \"detail\": \"The `feature-*` keys stay spread out and comparatively cooler, so they are useful as a low-priority reviewer note but often safe to collapse in tighter portfolio reports.\",\n                \"severity\": \"info\",\n                \"hotspot_keys\": [\"feature-0\", \"feature-1\"],\n                \"takeaway\": \"Use annotation filters or overflow summaries when you want to hide softer follow-up notes and keep the report focused on the highest-risk queues.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hot services for each synthetic latency family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Healthy service spread\",\n                \"detail\": \"The default balanced latency family rotates evenly across four APIs, so reducer load should stay close while the output still looks like a small production stack.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the calm baseline before introducing latency hotspots or on-call incident narratives.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Edge API hotspot\",\n                \"detail\": \"`edge-api` is intentionally heavier and slower here, so the hottest reducer should read like a front-door latency spike instead of a partitioning accident.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"edge-api\"],\n                \"takeaway\": \"This is the simplest observability-style story for discussing why p95 matters more than the mean under hotspot traffic.\",\n            },\n        ],\n        (\"balanced\", \"incident-spike\"): [\n            {\n                \"title\": \"Steady auth baseline\",\n                \"detail\": \"The balanced incident family keeps auth, cache, token, and profile services close enough that the report highlights normal service-to-service variance rather than an outage.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This is the before state for the incident-spike storyline.\",\n            },\n        ],\n        (\"skewed\", \"incident-spike\"): [\n            {\n                \"title\": \"Auth gateway timeout storm\",\n                \"detail\": \"`auth-gateway` dominates this family with elevated latency, so the hottest reducer should look like an outage-era timeout storm concentrated around one service.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"auth-gateway\"],\n                \"takeaway\": \"Call out the gap between average and p95 latency here to explain why long-tail spikes matter during incidents.\",\n            },\n            {\n                \"title\": \"Session cache spillover\",\n                \"detail\": \"`session-cache` forms the second-tier hotspot behind the auth gateway, which helps tell a broader bottleneck story about downstream spillover instead of a single bad node.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"session-cache\"],\n                \"takeaway\": \"Keep this annotation when you want a fuller causal narrative about cascading latency during the same incident.\",\n            },\n            {\n                \"title\": \"Profile path cool lane\",\n                \"detail\": \"`profile-read` stays comparatively cool, so it works as a low-priority contrast point or a card to collapse in tighter portfolio reports.\",\n                \"severity\": \"info\",\n                \"hotspot_keys\": [\"profile-read\"],\n                \"takeaway\": \"Use annotation filtering when you want the report to focus only on the riskiest paths.\",\n            },\n        ],\n        (\"balanced\", \"batch-window\"): [\n            {\n                \"title\": \"Even batch cadence\",\n                \"detail\": \"The balanced batch-window family rotates evenly across warehouse, indexing, backfill, and metrics jobs so the reducer heatmap reflects a normal overnight data window.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This family is useful when you want a data-engineering story rather than an incident-response story.\",\n            },\n        ],\n        (\"skewed\", \"batch-window\"): [\n            {\n                \"title\": \"Warehouse loader saturation\",\n                \"detail\": \"`warehouse-loader` is intentionally the hottest and slowest key here, so the benchmark looks like a batch-window saturation problem during an oversized ingest run.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"warehouse-loader\"],\n                \"takeaway\": \"Use this family to talk about long-running ETL contention and why reducer skew can line up with operational bottlenecks.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` |
| `benchmark_note_hook_source_line` | `63` | `134` |
| `benchmark_note_hook_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203"` |
| `combiner` | `"plugins_average_score.combine_values"` | `"plugins_service_latency.combine_values"` |
| `combiner_doc_summary` | `"Merge shard-local sum/count objects before the final reduce step."` | `"Merge shard-local latency summaries before the final reduce step."` |
| `combiner_source_anchor` | `"plugins_average_score.py#L16-L20"` | `"plugins_service_latency.py#L49-L51"` |
| `combiner_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51"` |
| `combiner_source_excerpt` | `"def combine_values(_key, values):\n    \"\"\"Merge shard-local sum/count objects before the final reduce step.\"\"\"\n    total = sum(item[\"sum\"] for item in values)\n    count = sum(item[\"count\"] for item in values)\n    return {\"sum\": total, \"count\": count}"` | `"def combine_values(_key, values):\n    \"\"\"Merge shard-local latency summaries before the final reduce step.\"\"\"\n    return _merge_latency_values(values)"` |
| `combiner_source_line` | `16` | `49` |
| `combiner_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51"` |
| `mapper` | `"plugins_average_score.map_records"` | `"plugins_service_latency.map_records"` |
| `mapper_doc_summary` | `"Emit per-student sum/count records from comma-separated score lines."` | `"Parse comma-separated service/latency rows into partial latency summaries."` |
| `mapper_source_anchor` | `"plugins_average_score.py#L7-L13"` | `"plugins_service_latency.py#L33-L46"` |
| `mapper_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46"` |
| `mapper_source_excerpt` | `"def map_records(lines):\n    \"\"\"Emit per-student sum/count records from comma-separated score lines.\"\"\"\n    for line in lines:\n        if not line.strip():\n            continue\n        name, score = line.split(\",\", 1)\n        yield name.strip().lower(), {\"sum\": float(score), \"count\": 1}"` | `"def map_records(lines):\n    \"\"\"Parse comma-separated service/latency rows into partial latency summaries.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        service, latency_ms = stripped.split(\",\", maxsplit=1)\n        latency_value = round(float(latency_ms.strip()), 3)\n        yield service.strip().lower(), {\n            \"count\": 1,\n            \"sum_ms\": latency_value,\n            \"max_ms\": latency_value,\n            \"samples_ms\": [latency_value],\n        }"` |
| `mapper_source_line` | `7` | `33` |
| `mapper_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46"` |
| `module_doc_summary` | `"Average-score analytics plugin with synthetic cohort benchmark families."` | `"Service-latency summary plugin for observability-style benchmark demos."` |
| `name` | `"plugin-average-score"` | `"plugin-service-latency"` |
| `plugin` | `"projects/mini-mapreduce-lab/plugins_average_score.py"` | `"projects/mini-mapreduce-lab/plugins_service_latency.py"` |
| `reducer` | `"plugins_average_score.reduce_key"` | `"plugins_service_latency.reduce_key"` |
| `reducer_doc_summary` | `"Return a rounded average score for one student key."` | `"Return count, average, p95, and max latency for one service key."` |
| `reducer_source_anchor` | `"plugins_average_score.py#L23-L27"` | `"plugins_service_latency.py#L54-L64"` |
| `reducer_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64"` |
| `reducer_source_excerpt` | `"def reduce_key(_key, values):\n    \"\"\"Return a rounded average score for one student key.\"\"\"\n    total = sum(item[\"sum\"] for item in values)\n    count = sum(item[\"count\"] for item in values)\n    return round(total / count, 3) if count else 0.0"` | `"def reduce_key(_key, values):\n    \"\"\"Return count, average, p95, and max latency for one service key.\"\"\"\n    merged = _merge_latency_values(values)\n    count = int(merged[\"count\"])\n    average = round(float(merged[\"sum_ms\"]) / count, 3) if count else 0.0\n    return {\n        \"count\": count,\n        \"avg_ms\": average,\n        \"p95_ms\": _nearest_rank_percentile(merged[\"samples_ms\"], 95),\n        \"max_ms\": round(float(merged[\"max_ms\"]), 3),\n    }"` |
| `reducer_source_line` | `23` | `54` |
| `reducer_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64"` |

### Diff 2: `projects/mini-mapreduce-lab/plugins_service_latency.py` → `projects/mini-mapreduce-lab/plugins_top_score.py`
- Changed fields: `available_dataset_families, benchmark_generator, benchmark_generator_doc_summary, benchmark_generator_signature, benchmark_generator_source_anchor, benchmark_generator_source_commit_url, benchmark_generator_source_excerpt, benchmark_generator_source_line, benchmark_generator_source_url, benchmark_note_hook, benchmark_note_hook_doc_summary, benchmark_note_hook_signature, benchmark_note_hook_source_anchor, benchmark_note_hook_source_commit_url, benchmark_note_hook_source_excerpt, benchmark_note_hook_source_line, benchmark_note_hook_source_url, combiner, combiner_doc_summary, combiner_source_anchor, combiner_source_commit_url, combiner_source_excerpt, combiner_source_line, combiner_source_url, mapper, mapper_doc_summary, mapper_source_anchor, mapper_source_commit_url, mapper_source_excerpt, mapper_source_line, mapper_source_url, module_doc_summary, name, plugin, reducer, reducer_doc_summary, reducer_source_anchor, reducer_source_commit_url, reducer_source_excerpt, reducer_source_line, reducer_source_url`

| Field | Previous | Current |
| --- | --- | --- |
| `available_dataset_families` | `["default", "incident-spike", "batch-window"]` | `null` |
| `benchmark_generator` | `"plugins_service_latency.benchmark_records"` | `null` |
| `benchmark_generator_doc_summary` | `"Generate deterministic latency fixtures for multiple observability-style families."` | `null` |
| `benchmark_generator_signature` | `"benchmark_records(scenario, records, seed, dataset_family='default')"` | `null` |
| `benchmark_generator_source_anchor` | `"plugins_service_latency.py#L67-L131"` | `null` |
| `benchmark_generator_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131"` | `null` |
| `benchmark_generator_source_excerpt` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic latency fixtures for multiple observability-style families.\"\"\"\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n\n    families = {\n        \"default\": {\n            \"balanced\": [\n                (\"edge-api\", 82, 9),\n                (\"catalog-api\", 76, 8),\n                (\"checkout-api\", 88, 10),\n                (\"search-api\", 71, 7),\n            ],\n            \"skewed\": [\n                (\"edge-api\", 144, 26),\n                (\"catalog-api\", 84, 10),\n                (\"checkout-api\", 96, 12),\n                (\"search-api\", 74, 8),\n            ],\n        },\n        \"incident-spike\": {\n            \"balanced\": [\n                (\"auth-gateway\", 118, 12),\n                (\"session-cache\", 89, 8),\n                (\"token-service\", 102, 10),\n                (\"profile-read\", 78, 7),\n            ],\n            \"skewed\": [\n                (\"auth-gateway\", 236, 54),\n                (\"session-cache\", 148, 22),\n                (\"token-service\", 121, 14),\n                (\"profile-read\", 83, 9),\n            ],\n        },\n        \"batch-window\": {\n            \"balanced\": [\n                (\"warehouse-loader\", 264, 30),\n                (\"index-builder\", 221, 24),\n                (\"backfill-runner\", 246, 27),\n                (\"metrics-rollup\", 198, 21),\n            ],\n            \"skewed\": [\n                (\"warehouse-loader\", 462, 86),\n                (\"index-builder\", 274, 34),\n                (\"backfill-runner\", 318, 42),\n                (\"metrics-rollup\", 206, 25),\n            ],\n        },\n    }\n    if dataset_family not in families or scenario not in families[dataset_family]:\n        raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")\n\n    templates = families[dataset_family][scenario]\n    lines = []\n    for index in range(records):\n        service, base_ms, spread_ms = templates[index % len(templates)]\n        jitter = rng.randint(-spread_ms, spread_ms)\n        lines.append(f\"{service},{round(base_ms + jitter, 3)}\")\n    if scenario == \"skewed\":\n        hotspot = templates[0][0]\n        for index in range(max(1, records // 3)):\n            latency = templates[0][1] + templates[0][2] + rng.randint(18, 52)\n            lines[index] = f\"{hotspot},{round(latency, 3)}\"\n    return lines"` | `null` |
| `benchmark_generator_source_line` | `67` | `null` |
| `benchmark_generator_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131"` | `null` |
| `benchmark_note_hook` | `"plugins_service_latency.benchmark_notes"` | `null` |
| `benchmark_note_hook_doc_summary` | `"Describe the intended hot services for each synthetic latency family."` | `null` |
| `benchmark_note_hook_signature` | `"benchmark_notes(scenario, dataset_family='default')"` | `null` |
| `benchmark_note_hook_source_anchor` | `"plugins_service_latency.py#L134-L203"` | `null` |
| `benchmark_note_hook_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203"` | `null` |
| `benchmark_note_hook_source_excerpt` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hot services for each synthetic latency family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Healthy service spread\",\n                \"detail\": \"The default balanced latency family rotates evenly across four APIs, so reducer load should stay close while the output still looks like a small production stack.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Use this as the calm baseline before introducing latency hotspots or on-call incident narratives.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Edge API hotspot\",\n                \"detail\": \"`edge-api` is intentionally heavier and slower here, so the hottest reducer should read like a front-door latency spike instead of a partitioning accident.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"edge-api\"],\n                \"takeaway\": \"This is the simplest observability-style story for discussing why p95 matters more than the mean under hotspot traffic.\",\n            },\n        ],\n        (\"balanced\", \"incident-spike\"): [\n            {\n                \"title\": \"Steady auth baseline\",\n                \"detail\": \"The balanced incident family keeps auth, cache, token, and profile services close enough that the report highlights normal service-to-service variance rather than an outage.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This is the before state for the incident-spike storyline.\",\n            },\n        ],\n        (\"skewed\", \"incident-spike\"): [\n            {\n                \"title\": \"Auth gateway timeout storm\",\n                \"detail\": \"`auth-gateway` dominates this family with elevated latency, so the hottest reducer should look like an outage-era timeout storm concentrated around one service.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"auth-gateway\"],\n                \"takeaway\": \"Call out the gap between average and p95 latency here to explain why long-tail spikes matter during incidents.\",\n            },\n            {\n                \"title\": \"Session cache spillover\",\n                \"detail\": \"`session-cache` forms the second-tier hotspot behind the auth gateway, which helps tell a broader bottleneck story about downstream spillover instead of a single bad node.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"session-cache\"],\n                \"takeaway\": \"Keep this annotation when you want a fuller causal narrative about cascading latency during the same incident.\",\n            },\n            {\n                \"title\": \"Profile path cool lane\",\n                \"detail\": \"`profile-read` stays comparatively cool, so it works as a low-priority contrast point or a card to collapse in tighter portfolio reports.\",\n                \"severity\": \"info\",\n                \"hotspot_keys\": [\"profile-read\"],\n                \"takeaway\": \"Use annotation filtering when you want the report to focus only on the riskiest paths.\",\n            },\n        ],\n        (\"balanced\", \"batch-window\"): [\n            {\n                \"title\": \"Even batch cadence\",\n                \"detail\": \"The balanced batch-window family rotates evenly across warehouse, indexing, backfill, and metrics jobs so the reducer heatmap reflects a normal overnight data window.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This family is useful when you want a data-engineering story rather than an incident-response story.\",\n            },\n        ],\n        (\"skewed\", \"batch-window\"): [\n            {\n                \"title\": \"Warehouse loader saturation\",\n                \"detail\": \"`warehouse-loader` is intentionally the hottest and slowest key here, so the benchmark looks like a batch-window saturation problem during an oversized ingest run.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"warehouse-loader\"],\n                \"takeaway\": \"Use this family to talk about long-running ETL contention and why reducer skew can line up with operational bottlenecks.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` | `null` |
| `benchmark_note_hook_source_line` | `134` | `null` |
| `benchmark_note_hook_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203"` | `null` |
| `combiner` | `"plugins_service_latency.combine_values"` | `"plugins_top_score.combine_values"` |
| `combiner_doc_summary` | `"Merge shard-local latency summaries before the final reduce step."` | `"Keep the shard-local maximum score for one student key."` |
| `combiner_source_anchor` | `"plugins_service_latency.py#L49-L51"` | `"plugins_top_score.py#L16-L18"` |
| `combiner_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18"` |
| `combiner_source_excerpt` | `"def combine_values(_key, values):\n    \"\"\"Merge shard-local latency summaries before the final reduce step.\"\"\"\n    return _merge_latency_values(values)"` | `"def combine_values(_key, values):\n    \"\"\"Keep the shard-local maximum score for one student key.\"\"\"\n    return max(values)"` |
| `combiner_source_line` | `49` | `16` |
| `combiner_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18"` |
| `mapper` | `"plugins_service_latency.map_records"` | `"plugins_top_score.map_records"` |
| `mapper_doc_summary` | `"Parse comma-separated service/latency rows into partial latency summaries."` | `"Parse comma-separated score rows into integer leaderboard updates."` |
| `mapper_source_anchor` | `"plugins_service_latency.py#L33-L46"` | `"plugins_top_score.py#L6-L13"` |
| `mapper_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13"` |
| `mapper_source_excerpt` | `"def map_records(lines):\n    \"\"\"Parse comma-separated service/latency rows into partial latency summaries.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        service, latency_ms = stripped.split(\",\", maxsplit=1)\n        latency_value = round(float(latency_ms.strip()), 3)\n        yield service.strip().lower(), {\n            \"count\": 1,\n            \"sum_ms\": latency_value,\n            \"max_ms\": latency_value,\n            \"samples_ms\": [latency_value],\n        }"` | `"def map_records(lines):\n    \"\"\"Parse comma-separated score rows into integer leaderboard updates.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        name, score = stripped.split(\",\", maxsplit=1)\n        yield name.strip().lower(), int(score.strip())"` |
| `mapper_source_line` | `33` | `6` |
| `mapper_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13"` |
| `module_doc_summary` | `"Service-latency summary plugin for observability-style benchmark demos."` | `"Maximum-score reducer plugin for simple leaderboard-style demos."` |
| `name` | `"plugin-service-latency"` | `"plugin-max-score"` |
| `plugin` | `"projects/mini-mapreduce-lab/plugins_service_latency.py"` | `"projects/mini-mapreduce-lab/plugins_top_score.py"` |
| `reducer` | `"plugins_service_latency.reduce_key"` | `"plugins_top_score.reduce_key"` |
| `reducer_doc_summary` | `"Return count, average, p95, and max latency for one service key."` | `"Return the overall maximum score for one student key."` |
| `reducer_source_anchor` | `"plugins_service_latency.py#L54-L64"` | `"plugins_top_score.py#L21-L23"` |
| `reducer_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/5d6ac8f8b9261dfca592baec0caa2d1fb0b963ef/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23"` |
| `reducer_source_excerpt` | `"def reduce_key(_key, values):\n    \"\"\"Return count, average, p95, and max latency for one service key.\"\"\"\n    merged = _merge_latency_values(values)\n    count = int(merged[\"count\"])\n    average = round(float(merged[\"sum_ms\"]) / count, 3) if count else 0.0\n    return {\n        \"count\": count,\n        \"avg_ms\": average,\n        \"p95_ms\": _nearest_rank_percentile(merged[\"samples_ms\"], 95),\n        \"max_ms\": round(float(merged[\"max_ms\"]), 3),\n    }"` | `"def reduce_key(_key, values):\n    \"\"\"Return the overall maximum score for one student key.\"\"\"\n    return max(values)"` |
| `reducer_source_line` | `54` | `21` |
| `reducer_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23"` |

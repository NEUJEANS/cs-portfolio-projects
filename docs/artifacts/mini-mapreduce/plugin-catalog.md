# Mini MapReduce plugin inspection

- Plugin count: `4`
- Diff count: `0`

## Catalog quick links

- [`plugin-average-score`](plugin-pages/plugin-average-score.md) — Average-score analytics plugin with synthetic cohort benchmark families. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, exam-cram, project-week`)
- [`plugin-service-latency`](plugin-pages/plugin-service-latency.md) — Service-latency summary plugin for observability-style benchmark demos. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, incident-spike, batch-window`)
- [`plugin-sessionization`](plugin-pages/plugin-sessionization.md) — Sessionization analytics plugin for product-usage benchmark demos. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, exam-revision, launch-day`)
- [`plugin-max-score`](plugin-pages/plugin-max-score.md) — Maximum-score reducer plugin for simple leaderboard-style demos. (`3 hooks` · `no dataset families` · `commit pinned` · `github linked`; families: `-`)

## Plugin summary

| Name | Plugin | Commit | Summary | Mapper | Reducer | Combiner | Benchmark generator | Benchmark note hook | Dataset families |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `plugin-average-score` | `projects/mini-mapreduce-lab/plugins_average_score.py` | `ab1a55b71a0e` | Average-score analytics plugin with synthetic cohort benchmark families. | `plugins_average_score.map_records`<br><small>`map_records(lines)`<br>line 7<br>plugins_average_score.py#L7-L13<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13)<br>Emit per-student sum/count records from comma-separated score lines.</small> | `plugins_average_score.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 23<br>plugins_average_score.py#L23-L27<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27)<br>Return a rounded average score for one student key.</small> | `plugins_average_score.combine_values`<br><small>`combine_values(_key, values)`<br>line 16<br>plugins_average_score.py#L16-L20<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20)<br>Merge shard-local sum/count objects before the final reduce step.</small> | `plugins_average_score.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 30<br>plugins_average_score.py#L30-L60<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60)<br>Generate deterministic cohort score fixtures for benchmark scenarios.</small> | `plugins_average_score.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 63<br>plugins_average_score.py#L63-L132<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132)<br>Describe the intended hot keys for each synthetic benchmark family.</small> | `default, exam-cram, project-week` |
| `plugin-service-latency` | `projects/mini-mapreduce-lab/plugins_service_latency.py` | `ab1a55b71a0e` | Service-latency summary plugin for observability-style benchmark demos. | `plugins_service_latency.map_records`<br><small>`map_records(lines)`<br>line 33<br>plugins_service_latency.py#L33-L46<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46)<br>Parse comma-separated service/latency rows into partial latency summaries.</small> | `plugins_service_latency.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 54<br>plugins_service_latency.py#L54-L64<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64)<br>Return count, average, p95, and max latency for one service key.</small> | `plugins_service_latency.combine_values`<br><small>`combine_values(_key, values)`<br>line 49<br>plugins_service_latency.py#L49-L51<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51)<br>Merge shard-local latency summaries before the final reduce step.</small> | `plugins_service_latency.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 67<br>plugins_service_latency.py#L67-L131<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131)<br>Generate deterministic latency fixtures for multiple observability-style families.</small> | `plugins_service_latency.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 134<br>plugins_service_latency.py#L134-L203<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203)<br>Describe the intended hot services for each synthetic latency family.</small> | `default, incident-spike, batch-window` |
| `plugin-sessionization` | `projects/mini-mapreduce-lab/plugins_sessionization.py` | `ab1a55b71a0e` | Sessionization analytics plugin for product-usage benchmark demos. | `plugins_sessionization.map_records`<br><small>`map_records(lines)`<br>line 52<br>plugins_sessionization.py#L52-L62<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62)<br>Emit per-user session events from comma-separated user,timestamp,page rows.</small> | `plugins_sessionization.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 70<br>plugins_sessionization.py#L70-L91<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91)<br>Summarize session count, duration, and activity intensity for one user.</small> | `plugins_sessionization.combine_values`<br><small>`combine_values(_key, values)`<br>line 65<br>plugins_sessionization.py#L65-L67<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67)<br>Keep shard-local event batches JSON-safe before global sessionization.</small> | `plugins_sessionization.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 135<br>plugins_sessionization.py#L135-L206<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206)<br>Generate deterministic product-analytics event streams for sessionization demos.</small> | `plugins_sessionization.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 209<br>plugins_sessionization.py#L209-L278<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278)<br>Describe the intended hotspot users and browsing patterns for each family.</small> | `default, exam-revision, launch-day` |
| `plugin-max-score` | `projects/mini-mapreduce-lab/plugins_top_score.py` | `ab1a55b71a0e` | Maximum-score reducer plugin for simple leaderboard-style demos. | `plugins_top_score.map_records`<br><small>`map_records(lines)`<br>line 6<br>plugins_top_score.py#L6-L13<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13)<br>Parse comma-separated score rows into integer leaderboard updates.</small> | `plugins_top_score.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 21<br>plugins_top_score.py#L21-L23<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23)<br>Return the overall maximum score for one student key.</small> | `plugins_top_score.combine_values`<br><small>`combine_values(_key, values)`<br>line 16<br>plugins_top_score.py#L16-L18<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18)<br>Keep the shard-local maximum score for one student key.</small> | - | - | `-` |

## Hook source excerpts

### <a id="plugin-average-score"></a>`plugin-average-score`

- Repository commit: `ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3`
#### Mapper: `plugins_average_score.map_records`
- Source anchor: `plugins_average_score.py#L7-L13`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132>

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

- Repository commit: `ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3`
#### Mapper: `plugins_service_latency.map_records`
- Source anchor: `plugins_service_latency.py#L33-L46`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_service_latency.py#L33-L46>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_service_latency.py#L54-L64>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_service_latency.py#L49-L51>

```python
def combine_values(_key, values):
    """Merge shard-local latency summaries before the final reduce step."""
    return _merge_latency_values(values)
```

#### Benchmark generator: `plugins_service_latency.benchmark_records`
- Source anchor: `plugins_service_latency.py#L67-L131`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_service_latency.py#L67-L131>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_service_latency.py#L134-L203>

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

### <a id="plugin-sessionization"></a>`plugin-sessionization`

- Repository commit: `ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3`
#### Mapper: `plugins_sessionization.map_records`
- Source anchor: `plugins_sessionization.py#L52-L62`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62>

```python
def map_records(lines):
    """Emit per-user session events from comma-separated user,timestamp,page rows."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        user_id, timestamp, page = [part.strip() for part in stripped.split(",", maxsplit=2)]
        yield user_id.lower(), {
            "timestamp": _isoformat_z(_parse_timestamp(timestamp)),
            "page": page,
        }
```

#### Reducer: `plugins_sessionization.reduce_key`
- Source anchor: `plugins_sessionization.py#L70-L91`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91>

```python
def reduce_key(_key, values):
    """Summarize session count, duration, and activity intensity for one user."""
    merged = _merge_event_batches(values)
    events = merged["events"]
    sessions = _session_summaries(events)
    durations = []
    for session in sessions:
        start = _parse_timestamp(session[0]["timestamp"])
        end = _parse_timestamp(session[-1]["timestamp"])
        durations.append(round((end - start).total_seconds() / 60, 3))
    total_events = len(events)
    session_count = len(sessions)
    return {
        "session_count": session_count,
        "total_events": total_events,
        "avg_events_per_session": round(total_events / session_count, 3) if session_count else 0.0,
        "avg_session_minutes": round(sum(durations) / session_count, 3) if session_count else 0.0,
        "longest_session_events": max((len(session) for session in sessions), default=0),
        "longest_session_minutes": max(durations, default=0.0),
        "first_event_at": events[0]["timestamp"] if events else None,
        "last_event_at": events[-1]["timestamp"] if events else None,
    }
```

#### Combiner: `plugins_sessionization.combine_values`
- Source anchor: `plugins_sessionization.py#L65-L67`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67>

```python
def combine_values(_key, values):
    """Keep shard-local event batches JSON-safe before global sessionization."""
    return {"events": sorted(values, key=lambda event: event["timestamp"])}
```

#### Benchmark generator: `plugins_sessionization.benchmark_records`
- Source anchor: `plugins_sessionization.py#L135-L206`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206>

```python
def benchmark_records(scenario, records, seed, dataset_family="default"):
    """Generate deterministic product-analytics event streams for sessionization demos."""
    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    base_time = datetime(2026, 4, 17, 8, 0, tzinfo=timezone.utc)

    families = {
        "default": {
            "balanced": [
                {"user": "student-alpha", "weight": 1.0, "session_size": 3, "session_gap": 52, "intra_gap": 5, "pages": ["home", "lecture-notes", "quiz"]},
                {"user": "student-beta", "weight": 1.0, "session_size": 3, "session_gap": 48, "intra_gap": 4, "pages": ["home", "lab", "forum"]},
                {"user": "student-gamma", "weight": 1.0, "session_size": 4, "session_gap": 56, "intra_gap": 5, "pages": ["home", "editor", "submissions"]},
                {"user": "student-delta", "weight": 1.0, "session_size": 3, "session_gap": 50, "intra_gap": 4, "pages": ["home", "flashcards", "quiz"]},
            ],
            "skewed": [
                {"user": "student-alpha", "weight": 3.3, "session_size": 5, "session_gap": 38, "intra_gap": 4, "pages": ["home", "lecture-notes", "quiz", "editor"]},
                {"user": "student-beta", "weight": 1.0, "session_size": 3, "session_gap": 55, "intra_gap": 5, "pages": ["home", "lab", "forum"]},
                {"user": "student-gamma", "weight": 0.9, "session_size": 3, "session_gap": 58, "intra_gap": 5, "pages": ["home", "editor", "submissions"]},
                {"user": "student-delta", "weight": 0.8, "session_size": 2, "session_gap": 62, "intra_gap": 6, "pages": ["home", "flashcards", "quiz"]},
            ],
        },
        "exam-revision": {
            "balanced": [
                {"user": "night-owl", "weight": 1.1, "session_size": 4, "session_gap": 46, "intra_gap": 4, "pages": ["review-guide", "quiz", "flashcards"]},
                {"user": "lab-partner", "weight": 1.0, "session_size": 3, "session_gap": 50, "intra_gap": 5, "pages": ["practice-exam", "solutions", "forum"]},
                {"user": "project-mate", "weight": 1.0, "session_size": 3, "session_gap": 54, "intra_gap": 5, "pages": ["review-guide", "editor", "submission"]},
                {"user": "commuter", "weight": 0.9, "session_size": 2, "session_gap": 58, "intra_gap": 6, "pages": ["flashcards", "quiz", "summary"]},
            ],
            "skewed": [
                {"user": "night-owl", "weight": 3.8, "session_size": 6, "session_gap": 34, "intra_gap": 4, "pages": ["review-guide", "quiz", "quiz-review", "flashcards"]},
                {"user": "lab-partner", "weight": 1.0, "session_size": 3, "session_gap": 52, "intra_gap": 5, "pages": ["practice-exam", "solutions", "forum"]},
                {"user": "project-mate", "weight": 0.9, "session_size": 3, "session_gap": 56, "intra_gap": 5, "pages": ["review-guide", "editor", "submission"]},
                {"user": "commuter", "weight": 0.7, "session_size": 2, "session_gap": 64, "intra_gap": 6, "pages": ["flashcards", "quiz", "summary"]},
            ],
        },
        "launch-day": {
            "balanced": [
                {"user": "release-lead", "weight": 1.1, "session_size": 4, "session_gap": 42, "intra_gap": 4, "pages": ["overview", "health", "errors", "deploy"]},
                {"user": "qa-desk", "weight": 1.0, "session_size": 3, "session_gap": 48, "intra_gap": 5, "pages": ["smoke-tests", "errors", "feedback"]},
                {"user": "support-ops", "weight": 1.0, "session_size": 3, "session_gap": 50, "intra_gap": 5, "pages": ["tickets", "feedback", "health"]},
                {"user": "analytics-watch", "weight": 0.9, "session_size": 3, "session_gap": 54, "intra_gap": 5, "pages": ["overview", "conversion", "health"]},
            ],
            "skewed": [
                {"user": "release-lead", "weight": 4.0, "session_size": 6, "session_gap": 31, "intra_gap": 4, "pages": ["overview", "health", "errors", "deploy", "rollback"]},
                {"user": "qa-desk", "weight": 1.1, "session_size": 4, "session_gap": 44, "intra_gap": 5, "pages": ["smoke-tests", "errors", "feedback"]},
                {"user": "support-ops", "weight": 1.0, "session_size": 3, "session_gap": 50, "intra_gap": 5, "pages": ["tickets", "feedback", "health"]},
                {"user": "analytics-watch", "weight": 0.8, "session_size": 2, "session_gap": 58, "intra_gap": 6, "pages": ["overview", "conversion", "health"]},
            ],
        },
    }
    if dataset_family not in families or scenario not in families[dataset_family]:
        raise ValueError(f"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}")

    profiles = families[dataset_family][scenario]
    counts = _allocate_counts(records, [profile["weight"] for profile in profiles])
    events = []
    for index, (profile, count) in enumerate(zip(profiles, counts)):
        start_offset = timedelta(minutes=(index * 9) + rng.randint(0, 4))
        events.extend(
            _generate_user_events(
                user=profile["user"],
                count=count,
                start_at=base_time + start_offset,
                session_size=profile["session_size"],
                session_gap_minutes=profile["session_gap"] + rng.randint(-3, 3),
                intra_gap_minutes=profile["intra_gap"],
                pages=profile["pages"],
            )
        )
    events.sort(key=lambda item: item["timestamp"])
    return [f"{event['user']},{event['timestamp']},{event['page']}" for event in events[:records]]
```

#### Benchmark note hook: `plugins_sessionization.benchmark_notes`
- Source anchor: `plugins_sessionization.py#L209-L278`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278>

```python
def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended hotspot users and browsing patterns for each family."""
    notes = {
        ("balanced", "default"): [
            {
                "title": "Even study cadence",
                "detail": "The default balanced family spreads activity across four students with similarly sized bursts, so reducer load should stay close while the output still demonstrates session boundaries.",
                "severity": "info",
                "takeaway": "Use this as the calm baseline before showing why repeated bursts from one user change the session story.",
            },
        ],
        ("skewed", "default"): [
            {
                "title": "Student alpha cram loop",
                "detail": "`student-alpha` revisits notes, quizzes, and the editor in repeated short bursts, so the hottest reducer should look like one user driving most session starts and events.",
                "severity": "watch",
                "hotspot_keys": ["student-alpha"],
                "takeaway": "This is the simplest sessionization story for discussing hot users versus evenly distributed class traffic.",
            },
        ],
        ("balanced", "exam-revision"): [
            {
                "title": "Shared review week",
                "detail": "The balanced exam family keeps revision activity spread across multiple learners and shorter study sessions, which makes the session summaries read like a healthy pre-exam baseline.",
                "severity": "info",
                "takeaway": "Good for explaining why session counts alone are not enough without session length and event intensity.",
            },
        ],
        ("skewed", "exam-revision"): [
            {
                "title": "Night-owl marathon",
                "detail": "`night-owl` owns most of the benchmark volume here with repeated late-session bursts, so the reducer heatmap should show one learner dominating both activity and longest-session metrics.",
                "severity": "risk",
                "hotspot_keys": ["night-owl"],
                "takeaway": "Call out how sessionization turns a raw clickstream into a workload story about sustained study behavior instead of isolated page hits.",
            },
            {
                "title": "Commuter quick checks",
                "detail": "`commuter` stays small and bursty, which makes it a useful low-priority contrast key when tightening the portfolio narrative down to the primary hotspot.",
                "severity": "info",
                "hotspot_keys": ["commuter"],
                "takeaway": "This annotation is a good candidate to collapse in portfolio-tight reports.",
            },
        ],
        ("balanced", "launch-day"): [
            {
                "title": "Coordinated launch monitoring",
                "detail": "The balanced launch-day family keeps release, QA, support, and analytics roles close enough that the session summary reads like a calm release checklist instead of an incident.",
                "severity": "info",
                "takeaway": "Use this as the before state for the launch-day hotspot story.",
            },
        ],
        ("skewed", "launch-day"): [
            {
                "title": "Release lead war room",
                "detail": "`release-lead` dominates this family with back-to-back dashboard, deploy, and rollback visits, so the hottest reducer should look like one operator repeatedly re-entering a release war room.",
                "severity": "risk",
                "hotspot_keys": ["release-lead"],
                "takeaway": "This turns the plugin into a product-analytics case study about launch-day behavior rather than generic score aggregation.",
            },
            {
                "title": "QA desk verification loop",
                "detail": "`qa-desk` forms a second-tier hotspot behind the release lead, which helps the report show supporting verification traffic instead of a single isolated key.",
                "severity": "watch",
                "hotspot_keys": ["qa-desk"],
                "takeaway": "Keep this note when you want a fuller multi-role launch narrative in the benchmark report.",
            },
        ],
    }
    return notes.get((scenario, dataset_family), [])
```

### <a id="plugin-max-score"></a>`plugin-max-score`

- Repository commit: `ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3`
#### Mapper: `plugins_top_score.map_records`
- Source anchor: `plugins_top_score.py#L6-L13`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23>

```python
def reduce_key(_key, values):
    """Return the overall maximum score for one student key."""
    return max(values)
```

#### Combiner: `plugins_top_score.combine_values`
- Source anchor: `plugins_top_score.py#L16-L18`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18>

```python
def combine_values(_key, values):
    """Keep the shard-local maximum score for one student key."""
    return max(values)
```

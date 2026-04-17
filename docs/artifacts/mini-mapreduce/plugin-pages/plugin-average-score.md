# Mini MapReduce plugin doc: `plugin-average-score`

## Snapshot

- Plugin path: `projects/mini-mapreduce-lab/plugins_average_score.py`
- Summary: Average-score analytics plugin with synthetic cohort benchmark families.
- Dataset families: `default, exam-cram, project-week`
- Catalog badges: `5 hooks` · `3 dataset families` · `commit pinned` · `github linked`
- Repository commit: `c0c005d1bcef0d903008fadbb7bd0f4faa872508`
- Catalog index: [plugin catalog](../plugin-catalog.md)
- Alternate format: [HTML](plugin-average-score.html)

## Hook summary

| Hook | Export | Signature | Details | Source |
| --- | --- | --- | --- | --- |
| Mapper | `plugins_average_score.map_records` | `map_records(lines)` | Emit per-student sum/count records from comma-separated score lines.<br>line 7<br>anchor `plugins_average_score.py#L7-L13` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13) |
| Reducer | `plugins_average_score.reduce_key` | `reduce_key(_key, values)` | Return a rounded average score for one student key.<br>line 23<br>anchor `plugins_average_score.py#L23-L27` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27) |
| Combiner | `plugins_average_score.combine_values` | `combine_values(_key, values)` | Merge shard-local sum/count objects before the final reduce step.<br>line 16<br>anchor `plugins_average_score.py#L16-L20` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20) |
| Benchmark generator | `plugins_average_score.benchmark_records` | `benchmark_records(scenario, records, seed, dataset_family='default')` | Generate deterministic cohort score fixtures for benchmark scenarios.<br>line 30<br>anchor `plugins_average_score.py#L30-L60` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60) |
| Benchmark note hook | `plugins_average_score.benchmark_notes` | `benchmark_notes(scenario, dataset_family='default')` | Describe the intended hot keys for each synthetic benchmark family.<br>line 63<br>anchor `plugins_average_score.py#L63-L132` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132) |

## Hook source excerpts

### Mapper: `plugins_average_score.map_records`

- Summary: Emit per-student sum/count records from comma-separated score lines.
- Source line: `7`
- Source anchor: `plugins_average_score.py#L7-L13`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13>

```python
def map_records(lines):
    """Emit per-student sum/count records from comma-separated score lines."""
    for line in lines:
        if not line.strip():
            continue
        name, score = line.split(",", 1)
        yield name.strip().lower(), {"sum": float(score), "count": 1}
```

### Reducer: `plugins_average_score.reduce_key`

- Summary: Return a rounded average score for one student key.
- Source line: `23`
- Source anchor: `plugins_average_score.py#L23-L27`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27>

```python
def reduce_key(_key, values):
    """Return a rounded average score for one student key."""
    total = sum(item["sum"] for item in values)
    count = sum(item["count"] for item in values)
    return round(total / count, 3) if count else 0.0
```

### Combiner: `plugins_average_score.combine_values`

- Summary: Merge shard-local sum/count objects before the final reduce step.
- Source line: `16`
- Source anchor: `plugins_average_score.py#L16-L20`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20>

```python
def combine_values(_key, values):
    """Merge shard-local sum/count objects before the final reduce step."""
    total = sum(item["sum"] for item in values)
    count = sum(item["count"] for item in values)
    return {"sum": total, "count": count}
```

### Benchmark generator: `plugins_average_score.benchmark_records`

- Summary: Generate deterministic cohort score fixtures for benchmark scenarios.
- Source line: `30`
- Source anchor: `plugins_average_score.py#L30-L60`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60>

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

### Benchmark note hook: `plugins_average_score.benchmark_notes`

- Summary: Describe the intended hot keys for each synthetic benchmark family.
- Source line: `63`
- Source anchor: `plugins_average_score.py#L63-L132`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132>

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

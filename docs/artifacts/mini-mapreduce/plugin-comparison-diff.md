# Mini MapReduce plugin inspection

- Plugin count: `2`
- Diff count: `1`

## Catalog quick links

- [`plugin-average-score`](#plugin-average-score) — Average-score analytics plugin with synthetic cohort benchmark families. (`5 hooks` · `3 dataset families` · `commit pinned` · `github linked`; families: `default, exam-cram, project-week`)
- [`plugin-max-score`](#plugin-max-score) — Maximum-score reducer plugin for simple leaderboard-style demos. (`3 hooks` · `no dataset families` · `commit pinned` · `github linked`; families: `-`)

## Plugin summary

| Name | Plugin | Commit | Summary | Mapper | Reducer | Combiner | Benchmark generator | Benchmark note hook | Dataset families |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `plugin-average-score` | `projects/mini-mapreduce-lab/plugins_average_score.py` | `2312cf246e3b` | Average-score analytics plugin with synthetic cohort benchmark families. | `plugins_average_score.map_records`<br><small>`map_records(lines)`<br>line 7<br>plugins_average_score.py#L7-L13<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13)<br>Emit per-student sum/count records from comma-separated score lines.</small> | `plugins_average_score.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 23<br>plugins_average_score.py#L23-L27<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27)<br>Return a rounded average score for one student key.</small> | `plugins_average_score.combine_values`<br><small>`combine_values(_key, values)`<br>line 16<br>plugins_average_score.py#L16-L20<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20)<br>Merge shard-local sum/count objects before the final reduce step.</small> | `plugins_average_score.benchmark_records`<br><small>`benchmark_records(scenario, records, seed, dataset_family='default')`<br>line 30<br>plugins_average_score.py#L30-L60<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60)<br>Generate deterministic cohort score fixtures for benchmark scenarios.</small> | `plugins_average_score.benchmark_notes`<br><small>`benchmark_notes(scenario, dataset_family='default')`<br>line 63<br>plugins_average_score.py#L63-L132<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132)<br>Describe the intended hot keys for each synthetic benchmark family.</small> | `default, exam-cram, project-week` |
| `plugin-max-score` | `projects/mini-mapreduce-lab/plugins_top_score.py` | `2312cf246e3b` | Maximum-score reducer plugin for simple leaderboard-style demos. | `plugins_top_score.map_records`<br><small>`map_records(lines)`<br>line 6<br>plugins_top_score.py#L6-L13<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13)<br>Parse comma-separated score rows into integer leaderboard updates.</small> | `plugins_top_score.reduce_key`<br><small>`reduce_key(_key, values)`<br>line 21<br>plugins_top_score.py#L21-L23<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23)<br>Return the overall maximum score for one student key.</small> | `plugins_top_score.combine_values`<br><small>`combine_values(_key, values)`<br>line 16<br>plugins_top_score.py#L16-L18<br>[github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18)<br>Keep the shard-local maximum score for one student key.</small> | - | - | `-` |

## Hook source excerpts

### <a id="plugin-average-score"></a>`plugin-average-score`

- Repository commit: `2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8`
#### Mapper: `plugins_average_score.map_records`
- Source anchor: `plugins_average_score.py#L7-L13`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132>

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

### <a id="plugin-max-score"></a>`plugin-max-score`

- Repository commit: `2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8`
#### Mapper: `plugins_top_score.map_records`
- Source anchor: `plugins_top_score.py#L6-L13`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13>

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
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23>

```python
def reduce_key(_key, values):
    """Return the overall maximum score for one student key."""
    return max(values)
```

#### Combiner: `plugins_top_score.combine_values`
- Source anchor: `plugins_top_score.py#L16-L18`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18>

```python
def combine_values(_key, values):
    """Keep the shard-local maximum score for one student key."""
    return max(values)
```


## Adjacent diffs

### Diff 1: `projects/mini-mapreduce-lab/plugins_average_score.py` → `projects/mini-mapreduce-lab/plugins_top_score.py`
- Changed fields: `available_dataset_families, benchmark_generator, benchmark_generator_doc_summary, benchmark_generator_signature, benchmark_generator_source_anchor, benchmark_generator_source_commit_url, benchmark_generator_source_excerpt, benchmark_generator_source_line, benchmark_generator_source_url, benchmark_note_hook, benchmark_note_hook_doc_summary, benchmark_note_hook_signature, benchmark_note_hook_source_anchor, benchmark_note_hook_source_commit_url, benchmark_note_hook_source_excerpt, benchmark_note_hook_source_line, benchmark_note_hook_source_url, combiner, combiner_doc_summary, combiner_source_anchor, combiner_source_commit_url, combiner_source_excerpt, combiner_source_url, mapper, mapper_doc_summary, mapper_source_anchor, mapper_source_commit_url, mapper_source_excerpt, mapper_source_line, mapper_source_url, module_doc_summary, name, plugin, reducer, reducer_doc_summary, reducer_source_anchor, reducer_source_commit_url, reducer_source_excerpt, reducer_source_line, reducer_source_url`

| Field | Previous | Current |
| --- | --- | --- |
| `available_dataset_families` | `["default", "exam-cram", "project-week"]` | `null` |
| `benchmark_generator` | `"plugins_average_score.benchmark_records"` | `null` |
| `benchmark_generator_doc_summary` | `"Generate deterministic cohort score fixtures for benchmark scenarios."` | `null` |
| `benchmark_generator_signature` | `"benchmark_records(scenario, records, seed, dataset_family='default')"` | `null` |
| `benchmark_generator_source_anchor` | `"plugins_average_score.py#L30-L60"` | `null` |
| `benchmark_generator_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60"` | `null` |
| `benchmark_generator_source_excerpt` | `"def benchmark_records(scenario, records, seed, dataset_family=\"default\"):\n    \"\"\"Generate deterministic cohort score fixtures for benchmark scenarios.\"\"\"\n    import random\n\n    if records <= 0:\n        raise ValueError(\"records must be positive\")\n    rng = random.Random(seed)\n\n    if dataset_family == \"default\":\n        if scenario == \"balanced\":\n            students = [f\"team-{index:02d}\" for index in range(12)]\n            return [f\"{students[index % len(students)]},{72 + ((index * 9) % 19)}\" for index in range(records)]\n        if scenario == \"skewed\":\n            hot_students = [\"capstone-core\"] * 16 + [f\"rotation-{index}\" for index in range(4)] + [f\"elective-{index}\" for index in range(10)]\n            return [f\"{rng.choice(hot_students)},{65 + rng.randint(0, 30)}\" for _ in range(records)]\n    elif dataset_family == \"exam-cram\":\n        if scenario == \"balanced\":\n            cohorts = [f\"study-group-{index:02d}\" for index in range(10)]\n            return [f\"{cohorts[index % len(cohorts)]},{78 + ((index * 7) % 15)}\" for index in range(records)]\n        if scenario == \"skewed\":\n            hot_students = [\"midterm-sprint\"] * 18 + [f\"review-{index}\" for index in range(4)] + [f\"prep-{index}\" for index in range(12)]\n            return [f\"{rng.choice(hot_students)},{70 + rng.randint(0, 25)}\" for _ in range(records)]\n    elif dataset_family == \"project-week\":\n        if scenario == \"balanced\":\n            squads = [f\"studio-{index:02d}\" for index in range(8)]\n            return [f\"{squads[index % len(squads)]},{74 + ((index * 5) % 21)}\" for index in range(records)]\n        if scenario == \"skewed\":\n            hot_students = [\"demo-day-core\"] * 12 + [f\"integration-{index}\" for index in range(6)] + [f\"feature-{index}\" for index in range(14)]\n            return [f\"{rng.choice(hot_students)},{68 + rng.randint(0, 28)}\" for _ in range(records)]\n\n    raise ValueError(f\"unsupported plugin benchmark scenario/family: {scenario}/{dataset_family}\")"` | `null` |
| `benchmark_generator_source_line` | `30` | `null` |
| `benchmark_generator_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L30-L60"` | `null` |
| `benchmark_note_hook` | `"plugins_average_score.benchmark_notes"` | `null` |
| `benchmark_note_hook_doc_summary` | `"Describe the intended hot keys for each synthetic benchmark family."` | `null` |
| `benchmark_note_hook_signature` | `"benchmark_notes(scenario, dataset_family='default')"` | `null` |
| `benchmark_note_hook_source_anchor` | `"plugins_average_score.py#L63-L132"` | `null` |
| `benchmark_note_hook_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132"` | `null` |
| `benchmark_note_hook_source_excerpt` | `"def benchmark_notes(scenario, dataset_family=\"default\"):\n    \"\"\"Describe the intended hot keys for each synthetic benchmark family.\"\"\"\n    notes = {\n        (\"balanced\", \"default\"): [\n            {\n                \"title\": \"Even cohort rotation\",\n                \"detail\": \"The default balanced cohort rotates evenly across team labels, so average-score aggregation stays spread out and mostly tests framework overhead rather than hot students.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"Treat any noticeable reducer imbalance here as partition spread, not as a workload-shaped hotspot.\",\n            },\n        ],\n        (\"skewed\", \"default\"): [\n            {\n                \"title\": \"Capstone leader hotspot\",\n                \"detail\": \"`capstone-core` is the dominant student key here, so the hottest reducer should look like one heavy project lead soaking up repeated score updates.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"capstone-core\"],\n                \"takeaway\": \"Use this scenario to explain how a single standout key can dominate reducer traffic even when the final averages remain correct.\",\n            },\n        ],\n        (\"balanced\", \"exam-cram\"): [\n            {\n                \"title\": \"Distributed study groups\",\n                \"detail\": \"Balanced exam-cram fixtures distribute scores across study groups, which makes them a clean baseline before simulating deadline pressure.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This is the calm comparison point for the cram-week hotspot run.\",\n            },\n        ],\n        (\"skewed\", \"exam-cram\"): [\n            {\n                \"title\": \"Cram-week surge\",\n                \"detail\": \"`midterm-sprint` is intentionally overrepresented, so the report should surface one study cohort as the obvious hotspot during cram-week traffic.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"midterm-sprint\"],\n                \"takeaway\": \"The skew should read like deadline-driven traffic, not like a partitioner bug.\",\n            },\n        ],\n        (\"balanced\", \"project-week\"): [\n            {\n                \"title\": \"Studio squad baseline\",\n                \"detail\": \"Balanced project-week fixtures rotate across studio squads so reducer load stays close even though the labels feel more portfolio-realistic than generic teams.\",\n                \"severity\": \"info\",\n                \"takeaway\": \"This family keeps the story portfolio-friendly without manufacturing a hotspot.\",\n            },\n        ],\n        (\"skewed\", \"project-week\"): [\n            {\n                \"title\": \"Demo-day crunch hotspot\",\n                \"detail\": \"`demo-day-core` is the main hotspot here, with integration and feature tails behind it, so you can narrate the skew as a deadline-driven project crunch.\",\n                \"severity\": \"risk\",\n                \"hotspot_keys\": [\"demo-day-core\", \"integration-0\", \"feature-0\"],\n                \"takeaway\": \"This slice is meant to read like a real project-week bottleneck where one squad absorbs the final demo push.\",\n            },\n            {\n                \"title\": \"Integration review backlog\",\n                \"detail\": \"The `integration-*` keys form a second-tier hotspot behind the demo-day core, which makes a good reviewer note when you want to talk about handoff queues instead of only the primary spike.\",\n                \"severity\": \"watch\",\n                \"hotspot_keys\": [\"integration-0\", \"integration-1\", \"integration-2\"],\n                \"takeaway\": \"Keep this card when you want a fuller systems story about follow-on bottlenecks after the main project crunch.\",\n            },\n            {\n                \"title\": \"Feature-lane tail\",\n                \"detail\": \"The `feature-*` keys stay spread out and comparatively cooler, so they are useful as a low-priority reviewer note but often safe to collapse in tighter portfolio reports.\",\n                \"severity\": \"info\",\n                \"hotspot_keys\": [\"feature-0\", \"feature-1\"],\n                \"takeaway\": \"Use annotation filters or overflow summaries when you want to hide softer follow-up notes and keep the report focused on the highest-risk queues.\",\n            },\n        ],\n    }\n    return notes.get((scenario, dataset_family), [])"` | `null` |
| `benchmark_note_hook_source_line` | `63` | `null` |
| `benchmark_note_hook_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L63-L132"` | `null` |
| `combiner` | `"plugins_average_score.combine_values"` | `"plugins_top_score.combine_values"` |
| `combiner_doc_summary` | `"Merge shard-local sum/count objects before the final reduce step."` | `"Keep the shard-local maximum score for one student key."` |
| `combiner_source_anchor` | `"plugins_average_score.py#L16-L20"` | `"plugins_top_score.py#L16-L18"` |
| `combiner_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18"` |
| `combiner_source_excerpt` | `"def combine_values(_key, values):\n    \"\"\"Merge shard-local sum/count objects before the final reduce step.\"\"\"\n    total = sum(item[\"sum\"] for item in values)\n    count = sum(item[\"count\"] for item in values)\n    return {\"sum\": total, \"count\": count}"` | `"def combine_values(_key, values):\n    \"\"\"Keep the shard-local maximum score for one student key.\"\"\"\n    return max(values)"` |
| `combiner_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L16-L20"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18"` |
| `mapper` | `"plugins_average_score.map_records"` | `"plugins_top_score.map_records"` |
| `mapper_doc_summary` | `"Emit per-student sum/count records from comma-separated score lines."` | `"Parse comma-separated score rows into integer leaderboard updates."` |
| `mapper_source_anchor` | `"plugins_average_score.py#L7-L13"` | `"plugins_top_score.py#L6-L13"` |
| `mapper_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13"` |
| `mapper_source_excerpt` | `"def map_records(lines):\n    \"\"\"Emit per-student sum/count records from comma-separated score lines.\"\"\"\n    for line in lines:\n        if not line.strip():\n            continue\n        name, score = line.split(\",\", 1)\n        yield name.strip().lower(), {\"sum\": float(score), \"count\": 1}"` | `"def map_records(lines):\n    \"\"\"Parse comma-separated score rows into integer leaderboard updates.\"\"\"\n    for raw in lines:\n        stripped = raw.strip()\n        if not stripped:\n            continue\n        name, score = stripped.split(\",\", maxsplit=1)\n        yield name.strip().lower(), int(score.strip())"` |
| `mapper_source_line` | `7` | `6` |
| `mapper_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13"` |
| `module_doc_summary` | `"Average-score analytics plugin with synthetic cohort benchmark families."` | `"Maximum-score reducer plugin for simple leaderboard-style demos."` |
| `name` | `"plugin-average-score"` | `"plugin-max-score"` |
| `plugin` | `"projects/mini-mapreduce-lab/plugins_average_score.py"` | `"projects/mini-mapreduce-lab/plugins_top_score.py"` |
| `reducer` | `"plugins_average_score.reduce_key"` | `"plugins_top_score.reduce_key"` |
| `reducer_doc_summary` | `"Return a rounded average score for one student key."` | `"Return the overall maximum score for one student key."` |
| `reducer_source_anchor` | `"plugins_average_score.py#L23-L27"` | `"plugins_top_score.py#L21-L23"` |
| `reducer_source_commit_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/2312cf246e3b3cab1fe7b3895bc7b55d7b60c3c8/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23"` |
| `reducer_source_excerpt` | `"def reduce_key(_key, values):\n    \"\"\"Return a rounded average score for one student key.\"\"\"\n    total = sum(item[\"sum\"] for item in values)\n    count = sum(item[\"count\"] for item in values)\n    return round(total / count, 3) if count else 0.0"` | `"def reduce_key(_key, values):\n    \"\"\"Return the overall maximum score for one student key.\"\"\"\n    return max(values)"` |
| `reducer_source_line` | `23` | `21` |
| `reducer_source_url` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L23-L27"` | `"https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23"` |

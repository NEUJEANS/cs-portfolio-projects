# Mini MapReduce plugin doc: `plugin-sessionization`

## Snapshot

- Plugin path: `projects/mini-mapreduce-lab/plugins_sessionization.py`
- Summary: Sessionization analytics plugin for product-usage benchmark demos.
- Dataset families: `default, exam-revision, launch-day`
- Catalog badges: `5 hooks` · `3 dataset families` · `commit pinned` · `github linked`
- Repository commit: `ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3`
- Catalog index: [plugin catalog](../plugin-catalog.md)
- Alternate format: [HTML](plugin-sessionization.html)

## Hook summary

| Hook | Export | Signature | Details | Source |
| --- | --- | --- | --- | --- |
| Mapper | `plugins_sessionization.map_records` | `map_records(lines)` | Emit per-user session events from comma-separated user,timestamp,page rows.<br>line 52<br>anchor `plugins_sessionization.py#L52-L62` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L52-L62) |
| Reducer | `plugins_sessionization.reduce_key` | `reduce_key(_key, values)` | Summarize session count, duration, and activity intensity for one user.<br>line 70<br>anchor `plugins_sessionization.py#L70-L91` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L70-L91) |
| Combiner | `plugins_sessionization.combine_values` | `combine_values(_key, values)` | Keep shard-local event batches JSON-safe before global sessionization.<br>line 65<br>anchor `plugins_sessionization.py#L65-L67` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67) |
| Benchmark generator | `plugins_sessionization.benchmark_records` | `benchmark_records(scenario, records, seed, dataset_family='default')` | Generate deterministic product-analytics event streams for sessionization demos.<br>line 135<br>anchor `plugins_sessionization.py#L135-L206` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L135-L206) |
| Benchmark note hook | `plugins_sessionization.benchmark_notes` | `benchmark_notes(scenario, dataset_family='default')` | Describe the intended hotspot users and browsing patterns for each family.<br>line 209<br>anchor `plugins_sessionization.py#L209-L278` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L209-L278) |

## Hook source excerpts

### Mapper: `plugins_sessionization.map_records`

- Summary: Emit per-user session events from comma-separated user,timestamp,page rows.
- Source line: `52`
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

### Reducer: `plugins_sessionization.reduce_key`

- Summary: Summarize session count, duration, and activity intensity for one user.
- Source line: `70`
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

### Combiner: `plugins_sessionization.combine_values`

- Summary: Keep shard-local event batches JSON-safe before global sessionization.
- Source line: `65`
- Source anchor: `plugins_sessionization.py#L65-L67`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/ab1a55b71a0eb4d40e3bf6e764ba90db78d0f2f3/projects/mini-mapreduce-lab/plugins_sessionization.py#L65-L67>

```python
def combine_values(_key, values):
    """Keep shard-local event batches JSON-safe before global sessionization."""
    return {"events": sorted(values, key=lambda event: event["timestamp"])}
```

### Benchmark generator: `plugins_sessionization.benchmark_records`

- Summary: Generate deterministic product-analytics event streams for sessionization demos.
- Source line: `135`
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

### Benchmark note hook: `plugins_sessionization.benchmark_notes`

- Summary: Describe the intended hotspot users and browsing patterns for each family.
- Source line: `209`
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

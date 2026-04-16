"""Average-score analytics plugin with synthetic cohort benchmark families."""

JOB_NAME = "plugin-average-score"
BENCHMARK_DATASET_FAMILIES = ["default", "exam-cram", "project-week"]


def map_records(lines):
    """Emit per-student sum/count records from comma-separated score lines."""
    for line in lines:
        if not line.strip():
            continue
        name, score = line.split(",", 1)
        yield name.strip().lower(), {"sum": float(score), "count": 1}


def combine_values(_key, values):
    """Merge shard-local sum/count objects before the final reduce step."""
    total = sum(item["sum"] for item in values)
    count = sum(item["count"] for item in values)
    return {"sum": total, "count": count}


def reduce_key(_key, values):
    """Return a rounded average score for one student key."""
    total = sum(item["sum"] for item in values)
    count = sum(item["count"] for item in values)
    return round(total / count, 3) if count else 0.0


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


def benchmark_notes(scenario, dataset_family="default"):
    """Describe the intended hot keys for each synthetic benchmark family."""
    notes = {
        ("balanced", "default"): [
            "The default balanced cohort rotates evenly across team labels, so average-score aggregation stays spread out and mostly tests framework overhead rather than hot students.",
        ],
        ("skewed", "default"): [
            "`capstone-core` is the dominant student key here, so the hottest reducer should look like one heavy project lead soaking up repeated score updates.",
        ],
        ("balanced", "exam-cram"): [
            "Balanced exam-cram fixtures distribute scores across study groups, which makes them a clean baseline before simulating deadline pressure.",
        ],
        ("skewed", "exam-cram"): [
            "`midterm-sprint` is intentionally overrepresented, so the report should surface one study cohort as the obvious hotspot during cram-week traffic.",
        ],
        ("balanced", "project-week"): [
            "Balanced project-week fixtures rotate across studio squads so reducer load stays close even though the labels feel more portfolio-realistic than generic teams.",
        ],
        ("skewed", "project-week"): [
            "`demo-day-core` is the main hotspot here, with integration and feature tails behind it, so you can narrate the skew as a deadline-driven project crunch.",
        ],
    }
    return notes.get((scenario, dataset_family), [])

JOB_NAME = "plugin-average-score"


def map_records(lines):
    for line in lines:
        if not line.strip():
            continue
        name, score = line.split(",", 1)
        yield name.strip().lower(), {"sum": float(score), "count": 1}


def combine_values(_key, values):
    total = sum(item["sum"] for item in values)
    count = sum(item["count"] for item in values)
    return {"sum": total, "count": count}


def reduce_key(_key, values):
    total = sum(item["sum"] for item in values)
    count = sum(item["count"] for item in values)
    return round(total / count, 3) if count else 0.0


def benchmark_records(scenario, records, seed, dataset_family="default"):
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

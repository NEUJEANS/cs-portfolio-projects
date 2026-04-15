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


def benchmark_records(scenario, records, seed):
    import random

    if records <= 0:
        raise ValueError("records must be positive")
    rng = random.Random(seed)
    if scenario == "balanced":
        students = [f"team-{index:02d}" for index in range(12)]
        return [f"{students[index % len(students)]},{72 + ((index * 9) % 19)}" for index in range(records)]
    if scenario == "skewed":
        hot_students = ["capstone-core"] * 16 + [f"rotation-{index}" for index in range(4)] + [f"elective-{index}" for index in range(10)]
        return [f"{rng.choice(hot_students)},{65 + rng.randint(0, 30)}" for _ in range(records)]
    raise ValueError(f"unsupported plugin benchmark scenario: {scenario}")

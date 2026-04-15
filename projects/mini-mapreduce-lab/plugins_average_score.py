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

JOB_NAME = "plugin-max-score"


def map_records(lines):
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        name, score = stripped.split(",", maxsplit=1)
        yield name.strip().lower(), int(score.strip())


def combine_values(_key, values):
    return max(values)


def reduce_key(_key, values):
    return max(values)

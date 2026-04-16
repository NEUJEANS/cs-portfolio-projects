"""Maximum-score reducer plugin for simple leaderboard-style demos."""

JOB_NAME = "plugin-max-score"


def map_records(lines):
    """Parse comma-separated score rows into integer leaderboard updates."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        name, score = stripped.split(",", maxsplit=1)
        yield name.strip().lower(), int(score.strip())


def combine_values(_key, values):
    """Keep the shard-local maximum score for one student key."""
    return max(values)


def reduce_key(_key, values):
    """Return the overall maximum score for one student key."""
    return max(values)

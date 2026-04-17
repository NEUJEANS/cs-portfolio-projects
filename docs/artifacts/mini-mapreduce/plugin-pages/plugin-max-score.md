# Mini MapReduce plugin doc: `plugin-max-score`

## Snapshot

- Plugin path: `projects/mini-mapreduce-lab/plugins_top_score.py`
- Summary: Maximum-score reducer plugin for simple leaderboard-style demos.
- Dataset families: `-`
- Catalog badges: `3 hooks` · `no dataset families` · `commit pinned` · `github linked`
- Repository commit: `c0c005d1bcef0d903008fadbb7bd0f4faa872508`
- Catalog index: [plugin catalog](../plugin-catalog.md)
- Alternate format: [HTML](plugin-max-score.html)

## Hook summary

| Hook | Export | Signature | Details | Source |
| --- | --- | --- | --- | --- |
| Mapper | `plugins_top_score.map_records` | `map_records(lines)` | Parse comma-separated score rows into integer leaderboard updates.<br>line 6<br>anchor `plugins_top_score.py#L6-L13` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13) |
| Reducer | `plugins_top_score.reduce_key` | `reduce_key(_key, values)` | Return the overall maximum score for one student key.<br>line 21<br>anchor `plugins_top_score.py#L21-L23` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23) |
| Combiner | `plugins_top_score.combine_values` | `combine_values(_key, values)` | Keep the shard-local maximum score for one student key.<br>line 16<br>anchor `plugins_top_score.py#L16-L18` | [github](https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18)<br>[commit](https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18) |

## Hook source excerpts

### Mapper: `plugins_top_score.map_records`

- Summary: Parse comma-separated score rows into integer leaderboard updates.
- Source line: `6`
- Source anchor: `plugins_top_score.py#L6-L13`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_top_score.py#L6-L13>

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

### Reducer: `plugins_top_score.reduce_key`

- Summary: Return the overall maximum score for one student key.
- Source line: `21`
- Source anchor: `plugins_top_score.py#L21-L23`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_top_score.py#L21-L23>

```python
def reduce_key(_key, values):
    """Return the overall maximum score for one student key."""
    return max(values)
```

### Combiner: `plugins_top_score.combine_values`

- Summary: Keep the shard-local maximum score for one student key.
- Source line: `16`
- Source anchor: `plugins_top_score.py#L16-L18`
- GitHub source: <https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18>
- GitHub source (commit pinned): <https://github.com/NEUJEANS/cs-portfolio-projects/blob/c0c005d1bcef0d903008fadbb7bd0f4faa872508/projects/mini-mapreduce-lab/plugins_top_score.py#L16-L18>

```python
def combine_values(_key, values):
    """Keep the shard-local maximum score for one student key."""
    return max(values)
```

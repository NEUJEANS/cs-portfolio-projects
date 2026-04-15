# 2026-04-15 mini-mapreduce plugin support research

## Why this slice
The project already demonstrated built-in jobs, reducer partitioning, and synthetic benchmarks. The next weak point was extensibility: every portfolio demo had to fit the built-in jobs. Adding plugin support makes the lab look more like a real mini framework.

## Brief external research
- Python's `importlib` docs recommend programmatic importing through import helpers rather than raw `__import__`.
- Dynamic modules created or loaded at runtime need explicit loader handling, and validation matters because a file may exist but still not expose the expected API.
- For a small portfolio lab, file-based plugins are simpler and more interview-friendly than packaging or entry-point discovery.

## Implementation choice
Keep the contract intentionally narrow:
- plugins are local Python files
- `map_records(lines)` yields `(key, int)` pairs
- `reduce_key(key, values)` returns one integer
- `JOB_NAME` is optional for nicer output

This is enough to show extensibility while preserving deterministic JSON output, reducer stats, and easy tests.

## Chosen example
A `plugins_top_score.py` example keeps the maximum score per user from `name,score` CSV lines. That showcases a reducer that is not plain summation, which makes the plugin path visibly meaningful.

## Follow-up ideas
- support loading plugins by module path or package entry point
- allow richer value types and reducer stats that do not assume additive outputs
- add multiple example plugins tied to realistic portfolio datasets

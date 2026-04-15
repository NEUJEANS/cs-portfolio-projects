# 2026-04-15 mini-mapreduce plugin refresh

## Refresher
- `importlib.util.spec_from_file_location` is the standard lightweight way to load a module from a file path.
- A dynamic import is not enough by itself; the loaded module still needs API validation.
- `callable(...)` checks keep the plugin contract explicit before execution.
- Reducer partitioning can stay deterministic even when the reducer logic changes.
- A plugin example should prove something the built-in reducer cannot do, otherwise extensibility looks fake.

## Self-test
- Why is a file-based plugin demo more convincing when the reducer performs `max` instead of `sum`?
- What should fail fast before any shard execution begins?
- Which parts of the pipeline should remain unchanged when a plugin is used?

## Self-test answers
- Because it demonstrates real customization of aggregation semantics, not just renamed word count.
- Missing plugin files, loader failures, or absent/non-callable `map_records` and `reduce_key` hooks.
- Sharding, stable partitioning, reducer bucket accounting, JSON rendering, and testable CLI behavior.

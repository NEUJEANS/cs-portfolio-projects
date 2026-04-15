# 2026-04-15 mini-mapreduce plugin inspection refresh

- `inspect.signature()` is useful when validating optional plugin hooks, but for human-readable diagnostics a stable `module.qualname` string is enough.
- A small JSON inspection payload should prefer declarative metadata (`mapper`, `reducer`, `combiner`, `benchmark_generator`, `available_dataset_families`) over raw source dumps so CLI output stays deterministic and diff-friendly.
- Self-test before coding: the inspection command should work for both file-based and importable-module plugins, and missing optional hooks should serialize as `null` instead of placeholder strings.

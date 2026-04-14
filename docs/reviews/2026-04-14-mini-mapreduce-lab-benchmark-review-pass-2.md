# mini-mapreduce-lab benchmark review pass 2

- Scope reviewed: validation paths and test coverage.
- Issue found: programmatic benchmark API did not reject non-positive `shard_size` even though the CLI guarded it.
- Fix applied: added `ValueError` validation inside `benchmark_wordcount()` and covered it in both project and repo-level tests.
- Result: CLI and programmatic behavior now match.

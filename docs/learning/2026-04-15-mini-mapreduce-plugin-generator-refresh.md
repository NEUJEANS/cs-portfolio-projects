# Mini MapReduce plugin generator refresh

## Scope
Short refresh before coding the plugin-defined benchmark generator slice.

## Refreshed points
- Optional plugin hooks should be validated the same way as mapper/reducer hooks: presence is optional, but if present they must be callable.
- Deterministic benchmark fixtures should keep the existing `(scenario, records, seed)` contract so benchmark artifacts stay reproducible.
- Generator output should be validated eagerly so bad plugins fail with a clear message before the benchmark pipeline runs.

## Self-test
- Proposed hook: `benchmark_records(scenario, records, seed) -> list[str]`
- Validation rule 1: every generated record must be a string
- Validation rule 2: the plugin must return exactly `records` lines
- Validation rule 3: built-in benchmark fixtures remain the fallback when the hook is absent

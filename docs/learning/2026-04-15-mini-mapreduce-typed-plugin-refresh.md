# mini-mapreduce typed plugin refresh

Date: 2026-04-15

## Refresh notes
- Python's `json.dumps()` works as a practical validation target for simple portfolio-safe output shapes.
- `numbers.Number` is a good numeric check for preserving descending sort on number-only outputs while excluding booleans from numeric ranking semantics.
- Structured combiners can safely aggregate shard-local objects like `{"sum": ..., "count": ...}` before the final reducer computes an average.

## Self-test
- Can a combiner emit a dict and a reducer emit a float while remaining JSON serializable? Yes.
- Should mixed output types be globally sorted by value? No; deterministic key ordering is safer unless every output is numeric.
- Should reducer workload stats depend on final reduced values? No; counting merged partial values is type-agnostic.

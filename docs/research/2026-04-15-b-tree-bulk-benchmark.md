# B-tree bulk-load benchmark notes — 2026-04-15

## Goal for this slice
Turn the previous bulk-loading feature into a measurable portfolio talking point by adding a reproducible benchmark path.

## Benchmark design chosen
- Compare two builds over the same strictly increasing key/value dataset.
- Baseline: generic `insert` path.
- Variant: append-oriented `bulk_load_sorted` path.
- Measure repeated wall-clock build times with `time.perf_counter_ns()` and report per-run plus average milliseconds.

## Why this design is good enough for the portfolio
- It isolates build-time behavior without adding external dependencies.
- It keeps the benchmark tied to the existing CLI and sample datasets.
- It verifies both build paths produce identical sorted items before reporting timings.

## Constraints to document
- Benchmark mode requires strictly increasing keys.
- Small datasets can produce noisy timings, so repeated runs matter more than a single number.
- This is a developer-facing microbenchmark, not a rigorous academic performance study.

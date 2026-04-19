# Regex engine benchmark slice research — 2026-04-19

## Brief source refresh
- Python's `re` docs confirm that `fullmatch(...)` and `search(...)` are the right standard-library entry points to compare against this lab's two public matching surfaces.
- Python's `time` docs still point to `time.perf_counter()` as the right monotonic high-resolution timer for short runtime comparisons.
- Because this lab intentionally implements ASCII teaching semantics for `\d`, `\w`, and `\s`, the benchmark cases should stay inside ASCII-only inputs so agreement checks are about engine behavior, not Unicode policy differences.

## Slice decision
Add a benchmark command that compares this lab with Python's `re` on safe regular-language cases.

Why this is the right next slice:
- it turns the project from "correct and explainable" into "correct, explainable, and performance-aware"
- it gives a compact interview story about validation, semantics agreement, and fair-enough microbenchmarking with reused compiled patterns
- it stays bounded: no new regex language surface is required, just better measurement and reporting around the surface the lab already supports

# Regex engine benchmark-suite refresh and self-test — 2026-04-19

## Refresh
- keep the suite file contract boring: one JSON object, one suite label, one `cases` array, and explicit per-case fields
- validate structure before running benchmarks so broken workload files fail fast with readable errors instead of half-written artifacts
- let CLI flags keep controlling `--iterations`, `--warmup`, and output paths so the suite file only describes the workload, not execution policy
- preserve the existing single-case and built-in sample-suite paths so the new feature adds flexibility without replacing simpler demos

## Self-test
1. What belongs in the suite file versus the CLI flags?
   - the suite file should describe benchmark cases; execution knobs like iteration count, warmup, and output destinations should stay in the CLI.
2. Why require each case to have its own `label`?
   - stable labels make reports, artifacts, and review comments easier to read than anonymous array positions.
3. What should happen if a suite file is malformed?
   - the command should exit cleanly with a specific validation error before any benchmark artifacts are written.

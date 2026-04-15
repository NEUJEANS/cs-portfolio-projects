# Review pass 1 - benchmark summary audit

## Focus
- check whether the benchmark output tells a complete load-factor story without needing post-processing

## Findings
1. The benchmark returned per-trial `load_factor` values, but the top-level summary omitted an aggregate achieved load factor.

## Fixes applied
- added `average_load_factor` to each benchmark summary row
- included the field in CSV export so spreadsheet charts can use it directly
- extended the benchmark unit test to verify the aggregate field is present

## Result
- benchmark output now exposes both target and achieved density at the summary level

# Regex engine benchmark tag-filter refresh and self-test — 2026-04-19

## Refresh
- keep benchmark tags as simple lowercase strings so they stay easy to type, diff, and reuse across JSON suite files and CLI flags
- normalize requested tags (`strip().lower()`) before filtering so repeated CLI usage is forgiving without making the data contract fuzzy
- keep filter semantics explicit: `--include-tag` means a case must contain every requested tag, while `--exclude-tag` removes any case containing one of those tags
- fail fast when filters remove every case or when the same tag is both included and excluded

## Self-test
1. Why use one tagged suite file instead of separate JSON files for each demo size?
   - one source of truth keeps workload definitions aligned while letting the CLI project different subsets on demand.
2. What should `--include-tag interview-demo --exclude-tag search` mean?
   - only keep cases tagged `interview-demo` and then remove any of those that also carry `search`.
3. What should happen when filters remove all cases?
   - the CLI should exit with a clean validation error instead of writing misleading empty reports.

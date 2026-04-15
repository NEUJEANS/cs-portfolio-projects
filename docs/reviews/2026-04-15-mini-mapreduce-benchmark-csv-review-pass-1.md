# Review pass 1 - mini-mapreduce benchmark CSV export

## Focus
- main CLI control flow after adding `--csv-output`
- regression risk for existing `run` subcommand

## Findings
1. Initial implementation accidentally accessed `args.csv_output` inside the `run` branch, which raised `AttributeError` for normal job execution.

## Fixes applied
- moved CSV writing logic into the `benchmark` branch only
- reran the full mini-mapreduce project + repo-level test suite after the fix

# Mini MapReduce heatmap export wrap-up

- Timestamp: 2026-04-15 09:25 UTC
- Project: `mini-mapreduce-lab`
- Commit hash: `199e272`

## What changed
- Added benchmark `heatmap_rows` to the JSON payload so shard-to-reducer skew is captured alongside timing metrics.
- Added `BenchmarkResult.heatmap_to_csv()` plus CLI support for `--heatmap-output`.
- Documented the new export flow in the project README and updated the project checklist.
- Added a short learning/self-test note for the deterministic CSV contract.
- Extended both project-level and repo-level tests to cover heatmap rendering and CLI output writing.

## Tests and reviews run
- `python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py tests/test_mini_mapreduce.py`
- Smoke-tested benchmark JSON/CSV/heatmap output with a temporary directory run.
- Review pass 1: checked the feature scope against the unfinished checklist item and ensured the slice stayed resumable.
- Review pass 2: inspected generated heatmap rows and fixed an inefficiency by precomputing shard partials instead of rebuilding them per reducer count.
- Review pass 3: reviewed the final diff for docs, CLI flags, and test coverage alignment.
- Secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- Turn the heatmap rows into Markdown/HTML chart artifacts so each benchmark run can produce portfolio-ready visuals automatically.

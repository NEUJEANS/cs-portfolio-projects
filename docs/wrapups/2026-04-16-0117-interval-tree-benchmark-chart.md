# Interval Tree Benchmark Chart Wrap-up

- Timestamp (UTC): 2026-04-16 01:17
- Project: `interval-tree-lab`
- Commit: `14a8329`

## What changed
- added `benchmark-chart` CLI support to render an SVG chart from the checked-in benchmark CSV artifact or a fresh benchmark series
- added CSV parsing and SVG rendering helpers so the chart step is reproducible and resumable
- generated and checked in `docs/artifacts/interval-tree-benchmark-series.svg` for README/portfolio embedding
- updated the interval-tree README, checklist, and learning notes for the new artifact flow
- added tests covering CSV parsing, SVG rendering, and CLI chart artifact generation

## Tests and reviews run
- `./.venv/bin/python -m pytest -q tests/test_interval_tree_lab.py`
- `python3 -m unittest projects/interval-tree-lab/test_interval_tree_lab.py`
- `python3 scripts/audit_interval_tree_readme_commands.py`
- review pass 1: compiled/ran the new command path and generated the SVG artifact
- review pass 2: inspected git diff for API/docs/test consistency
- review pass 3: ran `git diff --check`, checked `benchmark-chart --help`, and spot-checked the SVG header output
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add a second benchmark workload that mimics clustered meeting schedules so the chart can compare realistic interval distributions, not just uniform random ranges

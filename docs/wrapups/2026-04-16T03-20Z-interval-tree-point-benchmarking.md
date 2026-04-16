# interval-tree-lab wrap-up

- Timestamp: 2026-04-16 03:20 UTC
- Project: `interval-tree-lab`
- Commit: `e8da5e4`

## What changed
- added `--mode overlap|point` support to the interval-tree benchmark and benchmark-series workflows so the lab can measure both range-overlap and point-stabbing queries
- included query-mode metadata plus sample point probes in benchmark JSON/CSV payloads for reproducible portfolio evidence
- generated committed point-query benchmark CSV/JSON artifacts and an SVG chart for the README
- updated the README and checklist to document the new benchmark slice and resumable next step
- extended automated coverage for point benchmark helpers, CLI output, CSV parsing, and chart metadata

## Tests and reviews run
- `./.venv/bin/python -m pytest -q tests/test_interval_tree_lab.py`
- `python3 projects/interval-tree-lab/interval_tree_lab.py benchmark --mode point --intervals 200 --queries 50 --seed 23`
- `python3 scripts/audit_interval_tree_readme_commands.py`
- Review pass 1: performance review; cached the inorder interval list once for naive point benchmarking instead of rebuilding it on every query
- Review pass 2: artifact/readability review; made benchmark-chart subtitles and SVG descriptions aware of overlap vs point modes
- Review pass 3: docs consistency review; added README usage and checked-in artifact references for the new point-query evidence
- Secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` → clean

## Next step
- add schedule-window style workload generators so overlap and point benchmarks can compare realistic clustered booking data instead of only uniform random intervals

# Tarjan SCC bottleneck summaries wrap-up

- Timestamp: 2026-04-16 02:16 UTC
- Project: `tarjan-scc-lab`
- Commit shipped: `ba496c5`

## What changed
- added `incoming_component_count`, `outgoing_component_count`, and `bottleneck_role` to Tarjan SCC summary + condensation JSON output
- surfaced the new metadata in `explain` output for better interview/demo narration
- expanded README examples and notes so the portfolio story matches the implementation
- added targeted tests for source/bridge/sink/isolated labeling and recorded 3 review passes

## Tests and reviews run
- `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- review pass 1: correctness / shared bottleneck-role helper refactor
- review pass 2: CLI + README alignment
- review pass 3: regression re-run after refactor
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add topological ordering groups directly in condensation JSON for downstream tooling and richer visualization consumers

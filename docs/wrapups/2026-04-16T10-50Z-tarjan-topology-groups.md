# Tarjan SCC topology-groups wrap-up

- Timestamp: 2026-04-16 10:50 UTC
- Project: `tarjan-scc-lab`
- Commit shipped: `8fcc898`

## What changed
- added `topology_groups` to the Tarjan SCC `scc` and `condensation` JSON outputs so downstream tools get pre-grouped level layers directly
- included lightweight `component_ids` alongside duplicated component payloads for simpler consumers and link builders
- updated the README with a concrete grouped-JSON example and recorded the slice checklist, refresh note, and 3 review passes
- extended automated coverage for grouped topology output in direct function calls and CLI JSON flows

## Tests and reviews run
- `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python -m py_compile projects/tarjan-scc-lab/tarjan_scc_lab.py`
- `git diff --check`
- review pass 1: downstream JSON shape audit (`component_ids` added)
- review pass 2: docs + learning-note alignment after API change
- review pass 3: final CLI/regression sanity pass
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- export Tarjan vs. Kosaraju benchmark comparisons as CSV/markdown artifacts for portfolio screenshots

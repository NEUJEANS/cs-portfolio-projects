# Wrap-up - 2026-04-16T00:17Z - link-state-routing-lab

## What changed
- added a new `link-state-routing-lab` project with topology validation, LSA origination, flooding, LSDB handling, and Dijkstra-based forwarding tables
- added project docs: research note, learning refresh/self-test, checklist, README, and sample topology
- added targeted tests for shortest paths, stale LSA rejection, max-age withdrawal, reconvergence, and CLI JSON output
- updated the repo README and master checklist to include the new networking lab

## Tests and reviews run
- `./.venv/bin/python -m pytest -q projects/link-state-routing-lab/test_link_state_routing.py`
- `./.venv/bin/python projects/link-state-routing-lab/link_state_routing.py projects/link-state-routing-lab/sample_topology.json --source A`
- `./.venv/bin/python -m py_compile projects/link-state-routing-lab/link_state_routing.py`
- review pass 1: fixed mapping-iteration bug and flood-queue heap ordering bug
- review pass 2: CLI smoke/output audit
- review pass 3: docs/package/syntax audit
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit hash
- `1a96b6b` - Add link-state routing lab

## Next step
- add topology visualization and convergence comparison tooling so the link-state and distance-vector labs can be demonstrated side-by-side

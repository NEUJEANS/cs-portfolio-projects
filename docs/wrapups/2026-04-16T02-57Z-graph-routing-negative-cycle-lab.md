# graph-routing-negative-cycle-lab wrap-up

- Timestamp: 2026-04-16 02:57 UTC
- Project: `graph-routing-negative-cycle-lab`
- Commit: `af319b4`

## What changed
- added a new graph-routing lab that combines Bellman-Ford shortest paths, reachable negative-cycle detection, and Johnson all-pairs shortest paths
- added sample JSON fixtures for a routing graph with negative edges and a separate reachable negative-cycle graph
- added automated tests for shortest-path correctness, validation errors, negative-cycle reporting, and CLI output modes
- added research, learning, checklist, and three review-pass notes so the slice is resumable
- updated the root project index to include the new lab

## Tests and reviews run
- `./.venv/bin/python -m pytest tests/test_graph_routing_negative_cycle_lab.py tests -q`
- Review pass 1: diff audit; fixed a doc-to-output gap by surfacing `Iterations logged:` in pretty Bellman-Ford output
- Review pass 2: smoke-checked negative-cycle and Johnson CLI flows
- Review pass 3: docs/consistency grep across README, project files, checklist, and tests
- Secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` → clean

## Next step
- add graph-visual export (Mermaid or DOT) so shortest paths and detected negative cycles can be dropped directly into README demos

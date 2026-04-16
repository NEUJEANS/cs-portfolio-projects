# 2026-04-16 07:27 UTC — graph-routing Mermaid export slice

## What changed
- added Bellman-Ford shortest-path reconstruction helpers to support focused artifact rendering
- added `--export-mermaid` to `graph_routing_lab.py`
- exported `docs/artifacts/graph-routing-negative-cycle-sample.mmd`
- updated the project README plus slice checklist/learning/review notes

## Tests and reviews run
- `./.venv/bin/python -m pytest -q tests/test_graph_routing_negative_cycle_lab.py`
- `git diff --check`
- CLI smoke test for negative-cycle export to `/tmp/graph-routing-negative-cycle-demo.mmd`
- review pass 1: path reconstruction gap fixed
- review pass 2: CLI export workflow added
- review pass 3: Mermaid assertions/doc alignment fixed
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit hash
- implementation commit: `99cd3ca`

## Next step
- add DOT/Graphviz export or per-source Johnson path artifacts so the routing lab can show multiple visualization backends.

# 2026-04-16 03:37 UTC — link-state vs distance-vector comparison slice

## What changed
- added `--compare-distance-vector` flow to `projects/link-state-routing-lab/link_state_routing.py`
- compared link-state flood rounds against distance-vector convergence rounds on the same topology
- supported optional `--remove-link LEFT RIGHT` failure comparisons
- expanded link-state tests for direct API and CLI JSON comparison output
- updated the project README plus slice/learning notes for resumability

## Tests and reviews run
- `./.venv/bin/python -m pytest -q projects/link-state-routing-lab/test_link_state_routing.py projects/distance-vector-routing-lab/test_distance_vector_routing.py`
- review pass 1: `git diff --check`
- review pass 2: CLI smoke test for `--compare-distance-vector --remove-link B D`
- review pass 3: targeted diff review of changed files
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit hash
- implementation commit: `571720baccb643bd41e0d347f20fe51f21747a39`

## Next step
- export checked-in benchmark scenarios or artifacts from the new cross-lab comparison flow so the repo gains demo-ready comparison outputs, not just live JSON.

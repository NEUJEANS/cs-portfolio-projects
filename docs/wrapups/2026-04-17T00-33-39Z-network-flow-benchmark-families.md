# Network-flow benchmark families wrap-up

- Timestamp: 2026-04-17T00:33:39Z
- Project: `network-flow-lab`
- Implementation commit: `8aaf2b2e3dccc5a1cbec51be7ed9bbd623ee396b`

## What changed
- Added benchmark graph-family support to `network_flow.py` with `dag`, `dense`, and `layered` generators plus shared generator validation.
- Exposed `--graph-family` in the CLI, included per-trial density metadata, and improved benchmark docs so the new family options are demo-ready.
- Added generator/CLI regression tests, including coverage for family-specific minimum node requirements.
- Logged brief research notes and three review passes so the slice is resumable.
- Fixed a review-found usability issue where invalid benchmark-family node counts previously crashed with a Python traceback instead of a readable CLI error.

## Tests and reviews run
- `python3 -m unittest tests.test_network_flow_lab`
- `python3 -m py_compile projects/network-flow-lab/network_flow.py`
- `python3 projects/network-flow-lab/network_flow.py benchmark --nodes 24 --edge-probability 0.18 --trials 5 --seed 42 --pretty`
- `python3 projects/network-flow-lab/network_flow.py benchmark --graph-family dense --nodes 18 --edge-probability 0.30 --trials 3 --seed 7 --pretty`
- `python3 projects/network-flow-lab/network_flow.py benchmark --graph-family layered --nodes 18 --edge-probability 0.20 --trials 3 --seed 7 --pretty`
- `python3 projects/network-flow-lab/network_flow.py benchmark --graph-family layered --nodes 4 --trials 1 --seed 1`
- review pass 1: dense-family residual-edge audit
- review pass 2: CLI/docs/checklist consistency audit
- review pass 3: benchmark CLI failure-mode audit
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- Export one committed benchmark report card (Markdown plus SVG/CSV) so the new graph families show up as browsable portfolio artifacts without rerunning the CLI.

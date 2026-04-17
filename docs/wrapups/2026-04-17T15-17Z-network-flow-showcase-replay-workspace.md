# Network-flow showcase replay workspace

- Timestamp: `2026-04-17 15:17 UTC`
- Feature commit: `58e8559b2dced33c492c20922cbfec22332f5e1a`

## What changed
- Added a replay workspace to the network-flow showcase page so reviewers can:
  - edit the bundled sample flow graph JSON
  - copy/download a ready-to-run CLI command block
  - paste a fresh solver JSON payload back into the page
  - compare the fresh payload against the committed `sample-flow-result.json` reference on source/sink, max flow, min-cut partitions, and edge-flow table
- Added `build_flow_replay_reference(...)` to normalize committed/fresh flow payloads for comparison.
- Restored the weighted-assignment HTML/SVG helper functions after the in-progress local diff had dropped them during the replay-page edit.
- Made `showcase-demo` resilient when the committed flow JSON is unreadable by recomputing a fallback replay reference from `sample_graph.json` instead of crashing.
- Updated the network-flow checklist and README to advertise the new replayable showcase behavior.
- Regenerated `docs/artifacts/network-flow-lab/showcase.html` so the published artifact includes the new replay section.
- Added tests for replay-reference normalization and replay-related showcase HTML coverage.

## Tests and scans run
- `python3 -m unittest tests.test_network_flow_lab`
- `python3 -m py_compile projects/network-flow-lab/network_flow.py`
- `python3 projects/network-flow-lab/network_flow.py showcase-demo --artifact-dir docs/artifacts/network-flow-lab --html-out docs/artifacts/network-flow-lab/showcase.html`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Review passes
1. Diff review on `network_flow.py`, README, checklist, tests, and generated showcase HTML.
2. Static compile plus generated-artifact spot check for replay strings/command block.
3. Final git-state + remote-sync review after `git fetch origin` confirmed `main` was still aligned with `origin/main` before push.

## Next step
- Consider adding one or two preset “mutation ideas” in the replay workspace (for example: choke one cut edge or add a shortcut edge) so reviewers can trigger interesting max-flow changes without inventing edits from scratch.

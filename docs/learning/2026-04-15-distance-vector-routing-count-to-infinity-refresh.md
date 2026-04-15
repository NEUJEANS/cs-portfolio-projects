# Distance vector routing count-to-infinity refresh

## Goal
Add a stronger failure-story slice without turning the simulator into a full packet-level network emulator.

## Quick refresh
- Re-running Bellman-Ford from scratch on the failed topology is not enough for a count-to-infinity demo; the interesting behavior depends on stale routes that existed before the failure.
- A deterministic round-based model is still enough as long as the first post-failure round begins from the converged pre-failure tables.
- Markdown tables are the lightest export format for README/blog write-ups, while Mermaid sequence notes are useful for GitHub-rendered visual walkthroughs.

## Self-test
- Why did the earlier failure flow hide count-to-infinity? Because it recomputed initial tables from the already-broken topology, so stale routes never had a chance to propagate.
- What should round 0 of a failure timeline mean? The stable routing state immediately before the first reconvergence update on the failed topology.
- What is the minimal artifact that makes this slice portfolio-friendly? A focused destination timeline across a few routers rather than a full graph visualizer.

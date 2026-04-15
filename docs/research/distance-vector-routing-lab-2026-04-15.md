# Distance Vector Routing Lab Research — 2026-04-15

## Goal
Add a portfolio-grade networking/distributed-systems project that goes beyond static graph algorithms and demonstrates iterative convergence under topology changes.

## Brief findings
- Distance-vector routing is a strong teaching project because it shows decentralized convergence rather than one-shot shortest-path calculation.
- Bellman-Ford style updates are the core mechanism: each router revises a destination cost using direct-neighbor cost + neighbor-advertised cost.
- Split horizon hides routes from the neighbor they were learned from.
- Poison reverse advertises those same routes back with an infinite metric, making loop prevention easier to explain in demos.
- Link-failure simulation is important because routing behavior is most interesting during reconvergence, not just at steady state.

## Slice choice
Implement a deterministic simulator with:
- per-router routing tables
- round-based convergence
- optional split-horizon / poison-reverse advertisement rules
- topology mutation via link removal
- CLI-friendly JSON output for steady-state and reconvergence runs

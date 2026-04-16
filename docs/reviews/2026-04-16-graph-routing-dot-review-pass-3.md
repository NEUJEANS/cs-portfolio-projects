# Review pass 3 — graph-routing DOT slice

## Focus
Artifact/output smoke review using both the normal sample graph and the reachable negative-cycle graph.

## Issues found
1. The slice needed a committed sample DOT artifact, not just test coverage, so the project stays demo-ready from GitHub.
2. Negative-cycle artifact inspection confirmed the most important visual rule: cycle styling must override ordinary shortest-path highlighting when both apply.

## Fixes applied
- generated `docs/artifacts/graph-routing-negative-cycle-sample.dot` for the README/demo path
- verified and kept the precedence logic that renders cycle nodes/edges in red while preserving shortest-path highlighting elsewhere

# Refresh — Dinic + benchmarking notes

## Refresher
- Dinic alternates between:
  1. BFS to compute a level graph.
  2. DFS-style blocking-flow pushes that only follow edges to the next level.
- Compared with Edmonds-Karp, Dinic can send several augmenting paths within one BFS phase before rebuilding levels.
- For a benchmark intended for repeatable portfolio demos, deterministic graph generation and parity checks matter as much as raw timing.

## Self-test
- Could I explain why Dinic often beats Edmonds-Karp without overselling? Yes: it reduces repeated shortest-path searches by draining a whole level graph with blocking flow.
- Could I design a safe benchmark? Yes: fixed seed, explicit graph generator, same instances for both solvers, and fail if max-flow results diverge.
- Could this fit the existing project without bloating it? Yes: algorithm flag + single benchmark subcommand keeps the CLI coherent.

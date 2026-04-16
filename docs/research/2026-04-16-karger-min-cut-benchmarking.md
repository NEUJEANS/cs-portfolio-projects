# 2026-04-16 Karger min-cut benchmarking research

## Goal
Add a benchmark/reporting slice that makes the randomized nature of Karger's algorithm easier to discuss in a CS portfolio.

## Brief findings
- Repeated trials are the key story: the single-run success lower bound for basic Karger is only about `2 / (n * (n - 1))`, so benchmark output should foreground trial count and exact-hit rate.
- A small benchmark suite should mix graph families with different cut structure:
  - **cycle graphs** for a stable min cut of `2`
  - **complete graphs** for dense graphs with min cut `n - 1`
  - **barbell graphs** for an obvious bottleneck cut of `1`
  - **Erdos-Renyi random graphs** for less hand-crafted examples
- For portfolio-friendly artifact generation, it is useful to keep benchmark graphs small enough to cross-check against an exact solver or a known closed-form min cut.

## Sources checked
- Wikipedia summary of Karger's algorithm and repeated-trial probability framing
- lecture-note style references surfaced in search results for the `2 / (n(n-1))` lower bound
- general graph-family intuition for cycle, complete, barbell, and random graphs

## Implementation direction
- Add a `benchmark` CLI mode instead of a separate script so the project stays self-contained.
- Emit both JSON and CSV artifacts so README snippets and future charts can be derived from committed evidence.
- Keep Graphviz contraction snapshots as the next slice after benchmark/reporting lands.

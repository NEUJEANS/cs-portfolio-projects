# 2026-04-16 Karger min-cut benchmarking refresh

## Quick refresh
- Basic Karger contracts random edges until only two supernodes remain.
- The surviving parallel edges between the final supernodes define the cut size.
- Repeating the algorithm matters because one unlucky contraction of a true min-cut edge ruins that trial.
- Exact min-cut verification is still practical for small graphs and makes benchmark reporting much stronger.

## Mini self-test
1. **What is the min cut of a cycle graph with `n >= 3`?**
   - `2`
2. **What is the min cut of a complete graph with `n` vertices?**
   - `n - 1`
3. **Why is a barbell graph a nice benchmark case?**
   - It has a visually obvious bridge/bottleneck cut of `1`, so it is good for explaining what the algorithm is trying not to contract.
4. **What should benchmark output emphasize for a randomized algorithm?**
   - Trial count, exact-hit rate, and graph-family context rather than only one lucky best result.

## Decision
Use family-aware exact cut evaluation where possible so benchmark artifacts remain fast, deterministic, and easy to explain in the README.

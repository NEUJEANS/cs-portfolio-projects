# Splay Benchmark Refresh + Self-Test — 2026-04-15

## Topics refreshed
- how splaying trades extra rotations now for potentially cheaper future accesses
- how to compare self-adjusting trees against a fixed balanced BST without relying on noisy wall-clock timings
- deterministic workload generation with a fixed RNG seed
- dynamic module loading with `importlib.util`

## Mini self-test
### Q1. Why compare key comparisons instead of elapsed seconds?
Because comparison counts stay deterministic across runs and make tests stable, while short local timings are noisy.

### Q2. What workload should favor a splay tree?
A repeated hot-set or locality-heavy workload where the same few keys are accessed many times.

### Q3. What workload may favor a red-black tree?
Uniform random lookups, where the splay tree keeps paying extra restructuring cost without enough locality payoff.

### Q4. What integration gotcha mattered here?
When loading the sibling red-black module dynamically, the module must be placed into `sys.modules` before execution so decorators like `@dataclass` can resolve module metadata correctly.

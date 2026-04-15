# Chord random start-node sampling refresh — 2026-04-15

## Quick refresh
- Random benchmark sampling is useful only when it stays reproducible; the payload must record both the sampling mode and the seed.
- `random.sample` is a good fit here because it returns unique nodes without replacement, which keeps benchmark case counts predictable.
- Keeping the old `first` mode matters because it preserves backward-compatible demos and easy deterministic smoke tests.

## Self-test
- Q: Why record a separate `start_node_seed` when a main generator seed already exists?
  - A: It makes the start-node subset independently reproducible and lets future runs vary workload generation and sampling separately if needed.
- Q: Why not shuffle and slice the list inline every time?
  - A: A dedicated helper centralizes validation, clarifies the benchmark contract, and makes deterministic unit tests straightforward.

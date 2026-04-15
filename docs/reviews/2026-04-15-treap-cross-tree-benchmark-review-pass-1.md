# Review pass 1 — treap cross-tree benchmark

## Checks
- reviewed benchmark helper design against existing AVL/red-black/splay project APIs
- verified the benchmark uses deterministic insertion orders and a seeded successful-query workload

## Findings
- initial implementation needed an internal splay height helper because `splay-tree-lab` exposes no direct `height()` method
- fixed by computing height from the splay root during benchmarking

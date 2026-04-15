# 2026-04-15 interval-tree benchmark review pass 3

## What I reviewed
- correctness guardrails inside the benchmark loop
- README/test alignment with the new slice
- whether pruning evidence is visible without relying only on timing

## Result
- verified the benchmark checks interval-tree hits against naive-scan hits for every synthetic query
- verified tests cover both the direct benchmark helper and the CLI benchmark command
- verified the README now documents deterministic benchmarking and node-visit stats

## Additional fixes
- no further code changes were needed after pass 2

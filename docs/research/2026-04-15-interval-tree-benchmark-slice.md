# 2026-04-15 interval-tree benchmark slice research note

## Goal
Upgrade `interval-tree-lab` from a correctness-only data-structure demo into a stronger portfolio project that also explains *why* the augmentation matters in practice.

## Research summary
- Interval trees are typically justified by storing subtree `max_end` metadata so overlap searches can skip subtrees that cannot intersect the query.
- For portfolio value, it is not enough to claim pruning helps; the project should expose concrete evidence such as node-visit counts and a reproducible benchmark against a naive scan.
- A deterministic synthetic workload is a good fit for this repo because it keeps the slice self-contained, testable, and resumable without external datasets.

## Design chosen for this slice
- keep the existing closed-interval semantics and balanced bulk build
- add overlap-query stats that report how many tree nodes were visited
- add a benchmark command that generates deterministic synthetic intervals and queries from a seed
- compare interval-tree overlap results against a naive inorder scan on every benchmark query to guard against benchmark-only bugs
- report timing plus visit-ratio metrics so pruning behavior is visible even if wall-clock timing is noisy on shared hardware

## Notes
Web search was attempted for this slice but the provider was temporarily unavailable, so the implementation relies on standard interval-tree invariants and benchmark-design best practices rather than quoting fragile external claims.

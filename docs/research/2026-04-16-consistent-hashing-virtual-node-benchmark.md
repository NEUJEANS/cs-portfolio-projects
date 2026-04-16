# 2026-04-16 consistent-hashing virtual-node benchmark research note

## Goal
Upgrade `consistent-hashing-lab` from a correctness and remap demo into a stronger systems portfolio piece that also shows *why* virtual nodes matter.

## Research summary
- Virtual nodes are the standard way to smooth load distribution in consistent hashing because each physical node occupies many independent ring positions instead of one large contiguous range.
- For portfolio value, it is stronger to measure the effect than to state it abstractly, so a benchmark should compare imbalance metrics across several virtual-node counts with the same deterministic key workload.
- When topology changes are part of the story, benchmarking should also track remap movement ratios so the project can discuss balance and churn together.

## Design chosen for this slice
- keep the existing deterministic synthetic key generation so results stay reproducible and unit-test friendly
- add a `benchmark` CLI that accepts multiple virtual-node counts in one run
- report per-point imbalance metrics for the steady-state ring and optional movement metrics when adding or removing a node
- keep the output JSON-first so the series can feed later charting or markdown-export slices

## Notes
Web search was attempted for this slice, but the search provider was temporarily unavailable, so the design relies on standard consistent-hashing and benchmarking best practices already reflected in the project's earlier references.

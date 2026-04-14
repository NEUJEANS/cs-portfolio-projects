# Research — union-find-network-lab

## Goal
Add a fresh CS portfolio project after the existing set reached a strong completion bar.

## Notes
- DSU / union-find exposes three core operations: make-set, find, and union.
- The practical optimization pair is path compression plus union by rank/size.
- With both optimizations, amortized operation cost is effectively constant for portfolio-scale workloads.
- A good portfolio framing is dynamic network connectivity: merging service clusters, checking connectivity, and flagging redundant links that introduce cycles.

## Source used
- cp-algorithms: Disjoint Set Union overview and optimization notes (fetched 2026-04-14)

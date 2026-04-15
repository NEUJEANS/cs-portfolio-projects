# Interval Tree Lab Checklist

## Core implementation
- [x] Interval model with overlap and point-containment helpers
- [x] Balanced bulk-build flow for stable demos
- [x] Insert and delete while maintaining `max_end`
- [x] Overlap search, point search, validation, and JSON CLI output
- [x] Graphviz trace export for visited/pruned branch inspection
- [x] Benchmark command comparing interval-tree search vs naive scan
- [x] Benchmark-series command with JSON/CSV artifact output for portfolio-ready scaling snapshots

## Docs and portfolio polish
- [x] Project README with motivation, usage, design notes, and future ideas
- [x] Sample intervals artifact for quick demos
- [x] Add a checked-in benchmark-series artifact snapshot under `artifacts/`
- [x] Add a checked-in trace SVG/PNG example for README screenshots
- [x] Add a short complexity discussion section with best/average/worst-case intuition

## Validation
- [x] Unit tests for delete scenarios
- [x] Regression tests for benchmark-series helpers and CLI artifact writes
- [x] Add a smoke test for `trace --output` artifact creation
- [x] Add a lightweight README command audit script for docs drift

## Next slice ideas
- [ ] Plot CSV benchmark output into a small chart artifact for README embedding
- [x] Add an `explain` mode that narrates why branches were pruned for a single query
- [ ] Add workloads that model schedule windows vs random intervals for more realistic comparisons

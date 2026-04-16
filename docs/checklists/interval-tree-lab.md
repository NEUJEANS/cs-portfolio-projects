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
- [x] Plot CSV benchmark output into a small chart artifact for README embedding
- [x] Add an `explain` mode that narrates why branches were pruned for a single query
- [ ] Add workloads that model schedule windows vs random intervals for more realistic comparisons
- [x] Add point-query benchmark mode so stabbing queries have the same portfolio evidence as overlap queries

## Point-query benchmark slice (2026-04-16 03:11 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current interval-tree lab for the weakest unfinished benchmarking gap
- [x] skip web research because point stabbing benchmarks are a direct extension of the existing overlap benchmark harness
- [x] do a short Python CLI/benchmark self-check while planning the slice
- [x] update checklist/docs so the slice is resumable
- [x] add `--mode overlap|point` support to benchmark and benchmark-series flows
- [x] include query mode metadata plus point samples in JSON/CSV outputs for reproducible portfolio evidence
- [x] extend automated coverage for point benchmark helpers, CLI output, and CSV parsing
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

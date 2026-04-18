# Research — 2026-04-18 — page-replacement lab

## Why add this project now
The portfolio already had CPU scheduling, disk scheduling, cache simulation, and memory-allocation coverage, but it was still missing a focused virtual-memory paging project. A page-replacement simulator fills that gap cleanly and adds a classic OS interview topic with measurable algorithm tradeoffs.

## Brief external refresh
- reviewed the standard FIFO / LRU / OPT framing and Belady's anomaly references
- selected the classic reference string `1 2 3 4 1 2 5 1 2 3 4 5` because it is compact, interview-friendly, and demonstrates FIFO anomaly behavior across frame counts
- kept the first slice local/offline: deterministic simulation + CLI + JSON + anomaly study mode

## Slice goal
Ship a runnable initial project that lets a student:
1. simulate one algorithm with a readable trace,
2. compare FIFO/LRU/OPT on the same workload, and
3. study a frame range to surface FIFO Belady anomalies.

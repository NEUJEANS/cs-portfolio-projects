# Bloom filter CLI review pass 1 — 2026-04-14

## Focus
Code-path review of the new benchmark slice.

## Findings
1. Benchmark implementation originally materialized all inserted sample tokens in a list before insertion.
2. That worked for current test sizes but added avoidable memory overhead for larger demo runs.

## Fixes made
- Switched benchmark insertion to a generator expression so tokens stream directly into `extend()`.

## Result
- Benchmark behavior unchanged.
- Memory profile is cleaner for larger sample sizes.

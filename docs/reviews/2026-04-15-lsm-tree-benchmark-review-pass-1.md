# Review Pass 1 — lsm-tree-kv Bloom Filter Benchmark Slice

Date: 2026-04-15

## Focus
Benchmark design and correctness of the tradeoff story.

## Checks
- reviewed the new benchmark helper and CLI surface
- verified the output compares multiple bits-per-key settings in one run
- checked that the reported estimate uses the standard Bloom filter false-positive formula

## Issues found
- duplicate or out-of-order bits-per-key inputs would have produced repetitive or awkward output for README demos

## Fixes applied
- normalized bits-per-key options by sorting and deduplicating them before running the benchmark

## Outcome
The benchmark output is now stable and easier to read during walkthroughs.

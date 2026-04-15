# Review Pass 3 — lsm-tree-kv Bloom Filter Slice

Date: 2026-04-15

## Focus
Portfolio clarity, resumability, and documentation quality.

## Checks
- updated the project README so the new capability is visible to reviewers
- wrote research, learning, and checklist notes so the slice is resumable
- checked that the feature remains small and explainable for a student portfolio walkthrough
- confirmed future work still points toward sparse indexes, benchmarks, and background compaction

## Issues found
- none; docs and implementation are aligned

## Outcome
This is now a stronger systems project with a clear narrative: WAL + memtable + SSTables + Bloom-filter-assisted negative lookups.

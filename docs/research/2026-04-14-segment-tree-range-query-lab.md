# Segment Tree Range Query Lab - research notes

## Why this slice
The existing repo already covers many practical apps and several systems-heavy labs. A segment tree project adds a recognizable algorithms/data-structures artifact that interviewers immediately understand, but the lazy-propagation upgrade makes it stronger than a basic textbook implementation.

## Design notes
- store sum, min, and max so one traversal yields multiple useful aggregates
- use a separate lazy array for deferred range-add updates
- keep the CLI focused on explainable before/after output instead of benchmarking in this slice
- prefer a compact recursive implementation for readability and interview discussion value

## Scope for this run
- build from an input array
- support range query on `[l, r]`
- support lazy range-add updates
- expose a point-set helper implemented via range update logic
- ship tests for correctness and CLI behavior

## Follow-up ideas
- compare against Fenwick trees and prefix sums
- add iterative segment tree layout and memory/performance notes
- extend to range assignment or more advanced aggregates

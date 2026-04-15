# 2026-04-15 fenwick-tree-range-query-lab research

## Why this project
- the existing portfolio set already covers many core structures, so a Fenwick tree lab adds a compact but still interview-relevant range-query data structure
- it complements the existing segment tree project with a lighter-weight alternative that is often preferred for cumulative sums and frequency tables

## Notes from brief research
- cp-algorithms summarizes the classic Fenwick tree as a structure for O(log n) prefix/range queries and point updates using O(n) memory, originating from Peter M. Fenwick's cumulative frequency table paper
- the same reference highlights that one-based or zero-based variants are both viable; one-based indexing usually makes the lowbit transitions easier to explain in a teaching-oriented CLI project
- a stronger portfolio slice is not just point updates, but the dual-tree technique that supports range-add plus range-sum queries while keeping O(log n) operations

## Implementation direction
- use one-based indexing internally for clarity
- store user-facing values so snapshots are easy to inspect and reload
- expose build, sum, add, set, and export commands to keep the project demoable from the command line

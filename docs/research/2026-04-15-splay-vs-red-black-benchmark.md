# Splay vs Red-Black Benchmark Notes — 2026-04-15

## Why this slice
The existing `splay-tree-lab` had core CRUD-style tree operations but still lacked the strongest portfolio story: showing when self-adjusting behavior actually helps.

## Brief research takeaway
- Splay trees are most compelling under temporal locality and skewed hot-set access patterns.
- Red-black trees usually offer steadier worst-case behavior on uniform workloads because they stay balanced without restructuring on every search.
- A portfolio benchmark should therefore compare at least two workloads:
  - repeated hot-set lookups
  - uniform random successful lookups

## Slice decision
Add a deterministic benchmark command to `splay-tree-lab` that compares:
- splay-tree key comparisons and rotations
- red-black-tree key comparisons as a stable baseline
- the difference between hot-set and uniform-random workloads

## References
- https://www.cs.cmu.edu/~sleator/papers/self-adjusting.pdf
- https://www.cs.cornell.edu/courses/cs312/2007sp/lectures/lec24.html
- https://courses.cs.duke.edu/fall08/cps230/Lectures/L-09.pdf

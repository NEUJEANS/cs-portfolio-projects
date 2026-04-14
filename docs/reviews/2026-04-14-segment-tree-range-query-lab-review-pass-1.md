# Review pass 1 - segment-tree-range-query-lab

## Checks
- manual code review of update/query paths
- verified lazy-propagation invariants against CLI design

## Issue found
- `range_add` was mutating every covered element in `self.values`, which made a supposedly logarithmic update degrade toward linear time for large ranges.

## Fix applied
- removed per-element mutation from `range_add`
- added `materialize()` for debug/CLI output so core tree operations keep their intended asymptotic behavior

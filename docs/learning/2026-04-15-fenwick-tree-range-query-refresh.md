# 2026-04-15 Fenwick tree refresh and self-test

## Refresher
- `lowbit(i) = i & -i` isolates the least-significant set bit and determines the segment size represented at index `i`
- prefix sums walk downward by subtracting `lowbit(i)`
- point additions walk upward by adding `lowbit(i)`
- range sum = `prefix(right) - prefix(left - 1)`
- range-add + range-sum can be implemented with two Fenwick trees using the standard prefix reconstruction formula

## Self-test
1. Why is one-based indexing convenient here?
   - because lowbit jumps work cleanly without extra offset math in the traversal loops
2. How do you get an inclusive range sum?
   - subtract the prefix sum before the left boundary from the prefix sum at the right boundary
3. Why keep raw values in the snapshot even if the Fenwick arrays could also be stored?
   - because raw values are easier to inspect, validate, and rebuild deterministically on load

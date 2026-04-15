# 2026-04-15 interval tree refresh and self-test

## Refresher
- Interval trees answer overlap queries faster than naive scans by storing subtree metadata.
- The critical augmentation is `max_end`: the maximum high endpoint reachable under a node.
- If the left subtree's `max_end` is smaller than the query start, that left subtree cannot contain any overlap.
- Closed intervals `[a, b]` and `[c, d]` overlap when `a <= d` and `c <= b`.

## Self-test
1. Why is `max_end` enough to prune a subtree for overlap search?
   - Because if every interval in that subtree ends before the query starts, no overlap is possible there.
2. Why store intervals in deterministic sorted order?
   - It keeps builds, traversals, and tests stable and explainable.
3. What changes if intervals are half-open instead of closed?
   - The overlap predicate changes; endpoint-touching intervals may stop counting as collisions.

## Implementation reminders
- validate both BST ordering and metadata propagation
- include both interval-vs-interval and point stabbing examples
- reject exact duplicate intervals to keep demos deterministic

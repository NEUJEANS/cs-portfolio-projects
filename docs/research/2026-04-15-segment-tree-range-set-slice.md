# Segment tree range-set slice research

## Goal
Add a meaningful second lazy operation to the existing segment tree lab so the project covers a more realistic interview/system-design variant: overlapping range assignment and range increment updates.

## Notes
- Range-add alone only needs one pending delta tag.
- Range-set is stronger than range-add because it overwrites all prior values in the covered interval.
- When both operations exist, a pending set should dominate prior pending adds.
- A later add applied to a node with a pending set can be folded into the set value directly.
- On push-down, propagate pending set first, then any pending add.

## Slice choice
Upgrade the existing project instead of creating a brand new one because:
1. the project was already solid but still had a clear next-step weakness
2. this adds deeper DS reasoning without bloating the repo
3. it creates better interview discussion material around lazy-tag composition

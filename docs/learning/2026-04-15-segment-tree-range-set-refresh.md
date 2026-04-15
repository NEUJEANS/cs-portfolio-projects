# Segment tree range-set refresh + self-test

## Quick refresh
- `range_add(l, r, d)`: add `d` to sum, min, max for a fully covered node and accumulate lazy delta.
- `range_set(l, r, v)`: replace sum/min/max with values derived from `v`; clear additive lazy state because assignment overwrites prior increments.
- If a node already has a pending set and later receives an add, update the pending set value directly.
- Push order matters: propagate pending set before pending add so children inherit the correct base state.

## Self-test
1. If `[1,3,5,7]` gets `range_set(1,3,4)`, materialized values should become `[1,4,4,4]`.
2. If that result then gets `range_add(2,3,3)`, values should become `[1,4,7,7]`.
3. Querying `[1,3]` should then return `sum=18`, `min=4`, `max=7`.

## Expected implementation guardrails
- `point_set` should delegate to `range_set(i, i, value)`.
- Full-coverage updates should avoid descending further.
- Queries must still force push-down before partial traversal.

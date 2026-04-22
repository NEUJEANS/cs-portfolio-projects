# 2026-04-22 fenwick benchmark preset refresh

## Quick refresh
- Query-heavy workloads should make range-sum reads visibly dominate the operation mix.
- Update-heavy workloads should lean on range adds, not just point overwrites, because that is where the dual-tree Fenwick story is strongest.
- Point-set-heavy workloads are useful because they compress the gap between the Fenwick and segment-tree baselines and make the tradeoff story more honest.

## Self-test before implementation
- Make sure preset defaults still pass the existing ratio validation rules.
- Confirm preset metadata appears in every exported artifact format, not just JSON.
- Verify explicit ratio flags can still override preset defaults when a custom mix is needed.

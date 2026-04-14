# Python Refresh + Self-Test: Memory Allocator Simulator

## Refresh
- Use `dataclass(order=True)` sparingly; explicit sorting keys are clearer for block selection logic.
- Keep allocation strategy as a pure chooser over free blocks so tests can compare strategies deterministically.
- Model compaction as a rebuild of allocated blocks in address order, then append one final free block with remaining capacity.

## Self-test
- Q: What is external fragmentation in this simulator?
  - A: Free memory exists overall, but is split across holes so a large request may still fail.
- Q: Why can best-fit underperform first-fit on future requests?
  - A: It may create many tiny leftover holes that cannot satisfy later allocations.
- Q: What must compaction preserve?
  - A: Allocation sizes, ownership ids, total capacity, and relative order by address.

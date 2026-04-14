# Memory Allocator Simulator Research

## Goal
Build a portfolio-friendly simulator that demonstrates classic contiguous memory allocation strategies and the tradeoffs they create.

## Notes
- **First fit** places a request into the first free block large enough to satisfy it. It is fast and tends to keep search cost low.
- **Best fit** chooses the smallest usable free block, often reducing immediate waste but sometimes creating many tiny unusable holes.
- **Worst fit** chooses the largest free block, attempting to leave medium-sized gaps for future requests.
- Useful metrics for a teaching tool:
  - total allocated bytes
  - free bytes
  - number of holes
  - largest free block
  - external fragmentation indicator such as `free_bytes - largest_free_block`
- A compacting allocator can merge free space by shifting active allocations toward the front and updating their start addresses.

## Portfolio slice chosen
Implement a CLI/library that:
1. supports first-fit, best-fit, and worst-fit
2. supports allocate/free/compact operations
3. reports fragmentation and current layout
4. includes tests that compare strategy outcomes on the same workload

## Why this is a good student project
- demonstrates systems knowledge without needing kernel privileges
- creates clear algorithmic comparisons
- makes room for future visualization and workload replay features

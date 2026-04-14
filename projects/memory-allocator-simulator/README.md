# memory-allocator-simulator

A Python CLI that simulates contiguous memory allocation with **first-fit**, **best-fit**, and **worst-fit** strategies, plus free-space merging, compaction, and fragmentation metrics.

## Why it is portfolio-worthy
- demonstrates core operating-systems concepts in a runnable local program
- compares allocation policies on the same workload
- exposes fragmentation metrics and layout snapshots for discussion in interviews
- leaves room for future visualization and workload replay extensions

## Features
- allocate named blocks into a fixed-capacity address space
- free blocks and automatically merge adjacent holes
- compact active allocations to eliminate external fragmentation
- inspect memory layout and metrics as JSON
- script repeatable workloads from the command line

## Quick start
```bash
python3 memory_allocator.py \
  --capacity 32 \
  --strategy best-fit \
  --op alloc:A:8 \
  --op alloc:B:6 \
  --op alloc:C:4 \
  --op free:B \
  --op alloc:D:5 \
  --op compact \
  --pretty
```

## Example output
```json
{
  "metrics": {
    "capacity": 32,
    "strategy": "best-fit",
    "allocated_bytes": 17,
    "free_bytes": 15,
    "utilization": 0.5312,
    "hole_count": 1,
    "largest_free_block": 15,
    "external_fragmentation": 0
  }
}
```

## Allocation strategies
- **first-fit**: choose the first hole large enough for the request
- **best-fit**: choose the smallest hole that still fits the request
- **worst-fit**: choose the largest available hole

## Testing
```bash
python3 -m unittest projects/memory-allocator-simulator/test_memory_allocator.py
```

## Future improvements
- workload trace import/export
- terminal visualization of address-space evolution
- internal-fragmentation mode with alignment and page size constraints

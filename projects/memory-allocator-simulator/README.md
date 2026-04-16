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
- export per-step workload timelines as ASCII snapshots plus Markdown-ready summaries
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
  --timeline \
  --timeline-width 32 \
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
  },
  "timeline": [
    {
      "step": 0,
      "operation": "initial",
      "render": "................................"
    },
    {
      "step": 5,
      "operation": "alloc:D:5",
      "render": "AAAAAAAADDDDDCCCC..............."
    }
  ]
}
```

## Timeline export
Use `--timeline` to capture a snapshot after every operation. The JSON payload includes:
- `timeline`: per-step renders, layouts, and metrics for animation or inspection
- `timeline_markdown`: a Markdown table you can paste into notes, lab reports, or portfolio write-ups

The ASCII render uses `.` for free space and the first alphanumeric character of each allocation ID for occupied bytes (scaled down automatically for larger capacities).

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

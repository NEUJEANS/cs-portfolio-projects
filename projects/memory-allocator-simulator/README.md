# memory-allocator-simulator

A Python CLI that simulates contiguous memory allocation with **first-fit**, **best-fit**, and **worst-fit** strategies, plus free-space merging, compaction, fragmentation metrics, and optional alignment-aware internal fragmentation.

## Why it is portfolio-worthy
- demonstrates core operating-systems concepts in a runnable local program
- compares allocation policies on the same workload
- exposes both external and internal fragmentation for discussion in interviews
- shows how alignment changes real memory usage even when requested payload stays the same
- leaves room for future visualization and workload replay extensions

## Features
- allocate named blocks into a fixed-capacity address space
- free blocks and automatically merge adjacent holes
- compact active allocations to eliminate external fragmentation
- simulate aligned allocations to model internal fragmentation slack
- inspect memory layout and metrics as JSON
- export per-step workload timelines as ASCII snapshots plus Markdown-ready summaries
- script repeatable workloads from the command line

## Quick start
```bash
python3 memory_allocator.py \
  --capacity 32 \
  --strategy best-fit \
  --alignment 4 \
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
    "alignment": 4,
    "requested_bytes": 17,
    "allocated_bytes": 20,
    "free_bytes": 12,
    "utilization": 0.625,
    "payload_utilization": 0.5312,
    "hole_count": 1,
    "largest_free_block": 12,
    "external_fragmentation": 0,
    "internal_fragmentation": 3
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
      "render": "AAAAAAAADDDDDDDDCCCC............"
    }
  ]
}
```

## Timeline export
Use `--timeline` to capture a snapshot after every operation. The JSON payload includes:
- `timeline`: per-step renders, layouts, and metrics for animation or inspection
- `timeline_markdown`: a Markdown table you can paste into notes, lab reports, or portfolio write-ups

The ASCII render uses `.` for free space and the first alphanumeric character of each allocation ID for occupied bytes (scaled down automatically for larger capacities).

## Alignment mode
Use `--alignment N` to round every allocation up to a multiple of `N` bytes.

Examples:
- request `5` bytes with `--alignment 4` -> occupies `8` bytes, internal fragmentation `3`
- request `8` bytes with `--alignment 4` -> occupies `8` bytes, internal fragmentation `0`

Per-allocation layout entries include:
- `requested_size`: original payload requested by the workload
- `size`: actual bytes reserved in memory after alignment rounding
- `internal_fragmentation`: slack bytes reserved but unused by that block

Aggregate metrics include both:
- `utilization`: allocated bytes / capacity
- `payload_utilization`: requested bytes / capacity

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
- page-size constraints and fixed-partition modes beyond simple alignment rounding

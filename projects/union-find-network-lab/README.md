# union-find-network-lab

A compact portfolio project that demonstrates the disjoint-set union (union-find) data structure for dynamic network connectivity analysis.

## Why it is portfolio-worthy
- implements path compression and union by rank for near-constant-time connectivity checks
- surfaces a practical use case: grouping services, users, or devices into connected components
- detects when a new edge creates a cycle inside an existing component
- includes a scriptable CLI so interviewers can replay scenarios quickly

## Features
- add nodes lazily during union/find operations
- union and connectivity queries
- component summaries with members, edge counts, and cycle flags
- aggregate stats for component count and largest cluster
- JSON script runner for repeatable demos

## Usage
```bash
python3 projects/union-find-network-lab/union_find_network.py --script projects/union-find-network-lab/sample_operations.json
```

Example output highlights:
- one connected component containing `api`, `worker`, `db`, and `cache`
- `has_cycle: true` after adding the redundant `api` ↔ `cache` edge
- aggregate network stats for node and component counts

## Test
```bash
python3 -m unittest projects/union-find-network-lab/test_union_find_network.py
```

## Future improvements
- ingest CSV edge lists and emit time-series connectivity snapshots
- compare union-find against BFS/DFS recomputation on large dynamic graphs
- add benchmark mode for random graph workloads

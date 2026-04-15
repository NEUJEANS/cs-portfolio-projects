# union-find-network-lab

A compact portfolio project that demonstrates the disjoint-set union (union-find) data structure for dynamic network connectivity analysis.

## Why it is portfolio-worthy
- implements path compression and union by rank for near-constant-time connectivity checks
- surfaces a practical use case: grouping services, users, or devices into connected components
- detects when a new edge creates a cycle inside an existing component
- supports both scripted demos and bulk CSV ingestion for more realistic datasets
- includes a reproducible benchmark mode for quick performance talking points in interviews

## Features
- add nodes lazily during union/find operations
- union and connectivity queries
- component summaries with members, edge counts, and cycle flags
- aggregate stats for component count and largest cluster
- JSON script runner for repeatable demos
- CSV edge import with `source,target` headers
- optional snapshots every _N_ imported edges to show connectivity growth over time
- seeded benchmark mode for repeatable random graph workloads

## Usage
### Scripted operations
```bash
python3 projects/union-find-network-lab/union_find_network.py \
  --script projects/union-find-network-lab/sample_operations.json
```

### Bulk CSV import
```bash
python3 projects/union-find-network-lab/union_find_network.py \
  --edges-csv projects/union-find-network-lab/sample_edges.csv \
  --snapshot-every 2
```

The CSV importer expects a header row with `source,target` columns and returns final component summaries plus optional progress snapshots.

### Reproducible benchmark
```bash
python3 projects/union-find-network-lab/union_find_network.py \
  --benchmark \
  --benchmark-nodes 1000 \
  --benchmark-edges 5000 \
  --benchmark-seed 7
```

This gives a quick benchmark payload with elapsed time, edges per second, detected cycle edges, and final component statistics.

## Test
```bash
python3 -m unittest projects/union-find-network-lab/test_union_find_network.py
```

## Interview talking points
- explain why union-find beats repeated BFS/DFS recomputation for dynamic connectivity updates
- show how cycle detection falls out naturally when an edge joins nodes already in the same component
- demo the CSV importer as a stepping stone from toy examples to infrastructure/social-network datasets
- mention the seeded benchmark mode as a reproducible way to compare future optimizations

## Future improvements
- export benchmark results as JSON/CSV artifacts for README charts
- compare union-find against BFS/DFS recomputation on the same synthetic workloads
- render component growth over time from CSV snapshot data

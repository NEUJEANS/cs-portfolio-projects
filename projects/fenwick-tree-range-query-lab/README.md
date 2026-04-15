# fenwick-tree-range-query-lab

A portfolio-ready Python lab for Binary Indexed Trees (Fenwick trees) that supports fast prefix sums, range sums, range additions, snapshot persistence, and CLI-based demos.

## Why it is interesting
- demonstrates a classic data structure for O(log n) updates and prefix/range queries
- includes the more interview-worthy dual-tree trick for range-add + range-sum support
- stays practical with snapshot files, CSV exports, and deterministic tests
- gives you a compact project to discuss bit tricks, cumulative frequency tables, and performance tradeoffs versus segment trees

## Features
- newline-delimited integer input format for quick local experiments
- point and range operations through a CLI
- JSON snapshot save/load workflow for resumable demos
- CSV export with prefix sums for visualization or spreadsheet inspection
- tests that cover core Fenwick behavior, persistence, and CLI workflows

## Usage

Build a snapshot from newline-delimited integers:

```bash
python3 fenwick_tree_range_query_lab.py build \
  --input sample_values.txt \
  --output artifacts/fenwick.json
```

Query an inclusive range sum:

```bash
python3 fenwick_tree_range_query_lab.py sum \
  --snapshot artifacts/fenwick.json \
  2 5
```

Add a delta to an inclusive range:

```bash
python3 fenwick_tree_range_query_lab.py add \
  --snapshot artifacts/fenwick.json \
  --output artifacts/fenwick-updated.json \
  3 6 4
```

Set a single index to a new value:

```bash
python3 fenwick_tree_range_query_lab.py set \
  --snapshot artifacts/fenwick-updated.json \
  --output artifacts/fenwick-adjusted.json \
  4 21
```

Export current values and prefix sums:

```bash
python3 fenwick_tree_range_query_lab.py export \
  --snapshot artifacts/fenwick-adjusted.json \
  --output artifacts/fenwick.csv
```

## Test

```bash
python3 -m unittest projects/fenwick-tree-range-query-lab/test_fenwick_tree_range_query_lab.py
```

## Future improvements
- add a benchmark command that compares Fenwick and segment tree throughput on the same workloads
- support floating-point values or generic monoids where inversion is available
- add matplotlib or mermaid visualizations of covered index ranges during updates

# Segment Tree Range Query Lab

A portfolio-ready data structures lab that implements a segment tree with lazy propagation for fast range aggregation, bulk increments, and bulk assignment updates.

## Why this project is portfolio-worthy
- shows you can turn an interview-heavy data structure into a polished, runnable artifact
- demonstrates `O(log n)` range queries and updates instead of rescanning full arrays
- includes two lazy operations (`range-add` and `range-set`), which makes the implementation more realistic than a toy tree
- creates strong talking points around interval decomposition, deferred work, and overlapping update semantics

## Features
- build a segment tree from an integer array
- query range sum, min, and max in one traversal
- apply range-add updates with lazy propagation
- apply range-set assignment updates while preserving correctness with future adds
- set a single index value through the same update machinery
- inspect results through a small JSON-friendly CLI
- bundled sample workflow for before/after state comparisons

## Project structure
- `segment_tree_lab.py` - segment tree implementation and CLI
- `test_segment_tree_lab.py` - unit + CLI tests

## Usage
Run from this directory.

### Run the sample
```bash
python3 segment_tree_lab.py sample --json
```

### Query a range
```bash
python3 segment_tree_lab.py query --numbers 5,2,8,6,1 --left 1 --right 3
```

### Apply a lazy range-add update
```bash
python3 segment_tree_lab.py range-add --numbers 1,3,5,7,9,11 --left 1 --right 4 --delta 2
```

### Apply a lazy range-set assignment
```bash
python3 segment_tree_lab.py range-set --numbers 1,3,5,7,9,11 --left 2 --right 4 --value 6
```

### Overwrite a single value
```bash
python3 segment_tree_lab.py point-set --numbers 4,4,4 --index 1 --value 10
```

## Testing
```bash
python3 -m unittest discover -s projects/segment-tree-range-query-lab -p 'test_*.py' -v
```

## Complexity
- build: `O(n)`
- range query: `O(log n)`
- range-add update with lazy propagation: `O(log n)`
- range-set update with lazy propagation: `O(log n)`
- materializing the full array for debug output: `O(n log n)` in this readable recursive version

## Interview talking points
- when segment trees beat prefix sums or Fenwick trees
- why lazy propagation is useful for bulk range updates
- why range assignment needs stronger state than a single additive lazy tag
- how deferred assignment and deferred addition interact when updates overlap
- what changes would be required for max-subarray queries, iterative layouts, or persistence

## Future improvements
- add an iterative array-backed variant for memory-layout comparisons
- benchmark query/update throughput against naive scans and Fenwick trees
- add ASCII visualization of the tree shape during queries
- extend the node payload for range gcd or maximum-subarray experiments

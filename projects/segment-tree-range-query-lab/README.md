# Segment Tree Range Query Lab

A portfolio-ready data structures lab that implements a segment tree with lazy propagation for fast range aggregation and bulk updates.

## Why this project is portfolio-worthy
- shows you can turn an interview-heavy data structure into a polished, runnable artifact
- demonstrates `O(log n)` range queries and updates instead of rescanning full arrays
- includes lazy propagation, which makes the implementation more interesting than a basic prefix-sum exercise
- creates good talking points around recursion trees, interval decomposition, and performance trade-offs

## Features
- build a segment tree from an integer array
- query range sum, min, and max in one traversal
- apply range-add updates with lazy propagation
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

### Apply a lazy range update
```bash
python3 segment_tree_lab.py range-add --numbers 1,3,5,7,9,11 --left 1 --right 4 --delta 2
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
- materializing the full array for debug output: `O(n log n)` in this readable recursive version

## Interview talking points
- when segment trees beat prefix sums or Fenwick trees
- why lazy propagation is useful for bulk range updates
- how interval splitting guarantees `O(log n)` visits per operation on balanced recursion paths
- what changes would be required for range assignment, max-subarray queries, or iterative tree layouts

## Future improvements
- add an iterative array-backed variant for memory-layout comparisons
- support range assignment and richer aggregate values
- benchmark against naive scans and prefix-sum strategies
- add ASCII visualization of the tree shape during queries

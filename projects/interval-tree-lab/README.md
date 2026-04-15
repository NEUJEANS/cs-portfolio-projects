# interval-tree-lab

A portfolio-friendly interval tree lab that supports overlap queries and point stabbing queries with `max_end` augmentation.

## Why it is interesting
- demonstrates a classic augmented search-tree technique instead of a plain BST or array scan
- shows how interval overlap search can prune whole subtrees using metadata
- connects directly to schedulers, booking systems, compilers, geometric search, and genomic range tooling
- makes an interview-heavy data structure concrete, inspectable, and testable

## Features
- immutable interval model with optional labels
- balanced bulk build from sorted unique intervals for stable demos
- incremental insert with `max_end` metadata refresh
- find any overlap, find all overlaps, and point stabbing queries
- reproducible synthetic benchmark that compares pruned interval-tree searches versus naive scans
- per-query node-visit stats for making pruning behavior visible in JSON output
- bundled `sample_intervals.json` artifact for quick inspection and demo data
- validation for BST ordering and `max_end` correctness
- JSON CLI output for demo, build, overlap, point, insert, trace, and benchmark flows
- Graphviz DOT query-trace export that highlights visited, pruned, and overlapping branches

## Usage

Run the bundled demo:

```bash
python3 projects/interval-tree-lab/interval_tree_lab.py demo
```

Build a tree from interval specs:

```bash
python3 projects/interval-tree-lab/interval_tree_lab.py build 0-3:warmup 5-8:backup 6-10:deploy 15-23:analytics
```

Find which intervals overlap a query:

```bash
python3 projects/interval-tree-lab/interval_tree_lab.py overlap 7-18 0-3:warmup 5-8:backup 6-10:deploy 15-23:analytics 17-19:alerts
```

Find which intervals contain a point:

```bash
python3 projects/interval-tree-lab/interval_tree_lab.py point 26 15-23:analytics 19-20:maintenance 25-30:etl 26-26:ping
```

Insert a new interval:

```bash
python3 projects/interval-tree-lab/interval_tree_lab.py insert 8-12:patch 0-3:warmup 5-8:backup 15-23:analytics
```

Benchmark interval-tree pruning against a naive scan:

```bash
python3 projects/interval-tree-lab/interval_tree_lab.py benchmark --intervals 800 --queries 400 --seed 11
```

Export a Graphviz DOT trace for one query (render later with Graphviz if desired):

```bash
python3 projects/interval-tree-lab/interval_tree_lab.py trace 7-18 0-3:warmup 5-8:backup 6-10:deploy 15-23:analytics 17-19:alerts
```

## Test

```bash
python3 -m unittest tests/test_interval_tree_lab.py
```

## Design notes
- Intervals are closed ranges `[start, end]`, so touching endpoints count as overlap.
- Nodes are ordered lexicographically by `(start, end, label)` to keep traversals deterministic.
- Each node stores the maximum `end` value in its subtree. During overlap search, if the left subtree's `max_end` is below the query start, that entire subtree can be skipped.
- Bulk builds use median splitting on the sorted interval list to avoid obviously skewed demo trees.
- Validation checks both BST ordering and `max_end` propagation so augmentation bugs are easy to catch.
- The benchmark uses a deterministic random seed, verifies interval-tree and naive-scan overlap results match, and reports average node visits to make pruning effectiveness inspectable instead of hand-wavy.
- The `trace` command exports DOT text rather than images so the project stays dependency-light while still supporting screenshots, diagrams, and interview walk-throughs.

## Future improvements
- add deletion with metadata repair
- add rendered SVG/PNG artifacts for a few canonical query traces
- add CSV/plot export for benchmark runs across multiple workload sizes

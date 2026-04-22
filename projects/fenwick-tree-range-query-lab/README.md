# fenwick-tree-range-query-lab

A portfolio-ready Python lab for Binary Indexed Trees (Fenwick trees) that supports fast prefix sums, range sums, range additions, snapshot persistence, CSV export, and a deterministic benchmark that compares the same mixed workload against a lazy segment tree.

## Why it is interesting
- demonstrates a classic data structure for O(log n) updates and prefix/range queries
- includes the more interview-worthy dual-tree trick for range-add + range-sum support
- now includes a direct lazy segment tree comparison, which makes the tradeoff story much stronger in interviews and portfolio writeups
- stays practical with snapshot files, CSV exports, and deterministic benchmark artifacts
- gives you a compact project to discuss bit tricks, cumulative frequency tables, and performance tradeoffs versus segment trees

## Features
- newline-delimited integer input format for quick local experiments
- point and range operations through a CLI
- JSON snapshot save/load workflow for resumable demos
- CSV export with prefix sums for visualization or spreadsheet inspection
- deterministic benchmark mode that replays the same mixed range-sum, range-add, and point-set workload through both a RangeFenwick implementation and a lazy segment tree baseline
- named benchmark presets for balanced, query-heavy, update-heavy, and point-set-heavy workload stories, with optional ratio overrides when you want to tune a preset further
- JSON, CSV, Markdown, and standalone SVG benchmark artifact export for README charts, blog posts, recruiter-ready notes, or slide screenshots
- tests that cover core Fenwick behavior, persistence, CLI workflows, mixed-structure correctness, and benchmark verification

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

Benchmark RangeFenwick against a lazy segment tree and save portfolio-ready artifacts:

```bash
python3 fenwick_tree_range_query_lab.py benchmark \
  --preset balanced \
  --size 256 \
  --operations 1000 \
  --repeats 3 \
  --seed 7 \
  --query-ratio 0.45 \
  --set-ratio 0.15 \
  --max-range-width 32 \
  --output ../../docs/artifacts/fenwick-tree-range-query-lab/sample-benchmark.json \
  --csv-output ../../docs/artifacts/fenwick-tree-range-query-lab/sample-benchmark.csv \
  --markdown-output ../../docs/artifacts/fenwick-tree-range-query-lab/sample-benchmark-report.md \
  --svg-output ../../docs/artifacts/fenwick-tree-range-query-lab/sample-benchmark-chart.svg
```

Generate a query-heavy variant of the same benchmark story:

```bash
python3 fenwick_tree_range_query_lab.py benchmark \
  --preset query-heavy \
  --size 256 \
  --operations 1000 \
  --repeats 3 \
  --seed 7 \
  --output ../../docs/artifacts/fenwick-tree-range-query-lab/presets/query-heavy-benchmark.json \
  --csv-output ../../docs/artifacts/fenwick-tree-range-query-lab/presets/query-heavy-benchmark.csv \
  --markdown-output ../../docs/artifacts/fenwick-tree-range-query-lab/presets/query-heavy-benchmark-report.md \
  --svg-output ../../docs/artifacts/fenwick-tree-range-query-lab/presets/query-heavy-benchmark-chart.svg
```

The benchmark validates correctness before comparing timing numbers, so the same report can support both engineering discussion and portfolio storytelling. Presets make it easier to show how Fenwick trees behave under different mixes instead of only one balanced workload, and the SVG export turns each deterministic payload into a screenshot-friendly chart with throughput and per-operation latency bars.

## Sample committed artifacts
- `docs/artifacts/fenwick-tree-range-query-lab/sample-benchmark.json`
- `docs/artifacts/fenwick-tree-range-query-lab/sample-benchmark.csv`
- `docs/artifacts/fenwick-tree-range-query-lab/sample-benchmark-report.md`
- `docs/artifacts/fenwick-tree-range-query-lab/sample-benchmark-chart.svg`
- `docs/artifacts/fenwick-tree-range-query-lab/presets/query-heavy-benchmark-report.md`
- `docs/artifacts/fenwick-tree-range-query-lab/presets/update-heavy-benchmark-report.md`
- `docs/artifacts/fenwick-tree-range-query-lab/presets/point-set-heavy-benchmark-report.md`

## Test

```bash
python3 -m unittest projects/fenwick-tree-range-query-lab/test_fenwick_tree_range_query_lab.py
```

## Future improvements
- support floating-point values or generic monoids where inversion is available
- add a multi-preset comparison dashboard so all workload presets can be contrasted in one recruiter-friendly artifact instead of separate files

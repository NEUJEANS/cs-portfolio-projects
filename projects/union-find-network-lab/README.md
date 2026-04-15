# union-find-network-lab

A compact portfolio project that demonstrates the disjoint-set union (union-find) data structure for dynamic network connectivity analysis.

## Why it is portfolio-worthy
- implements path compression and union by rank for near-constant-time connectivity checks
- surfaces a practical use case: grouping services, users, or devices into connected components
- detects when a new edge creates a cycle inside an existing component
- supports both scripted demos and bulk CSV ingestion for more realistic datasets
- includes reproducible benchmark and benchmark-series modes for quick performance talking points in interviews
- compares union-find against a full BFS recomputation baseline on the exact same random edge stream for stronger algorithmic storytelling
- can export committed JSON/CSV artifacts that plug directly into README charts or portfolio writeups
- can now generate a ready-to-embed Markdown summary from the recomputation comparison artifact for README/blog reuse
- now renders standalone SVG charts from benchmark, CSV-import, or comparison artifacts without pulling in plotting dependencies

## Features
- add nodes lazily during union/find operations
- union and connectivity queries
- component summaries with members, edge counts, and cycle flags
- aggregate stats for component count and largest cluster
- JSON script runner for repeatable demos
- CSV edge import with `source,target` headers
- optional snapshots every _N_ imported edges to show connectivity growth over time
- seeded benchmark mode for repeatable random graph workloads
- benchmark-series mode that sweeps multiple edge counts in one command
- comparison mode that replays the same random edges through union-find and a full BFS recomputation baseline
- JSON and CSV artifact export for committed sample reports
- Markdown summary export for connectivity comparison artifacts
- SVG chart export for benchmark-series throughput, CSV-import component-growth, and comparison artifacts
- chart rendering from existing `.json` or `.csv` artifacts via `--chart-input`

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

### Benchmark-series export for portfolio artifacts
```bash
python3 projects/union-find-network-lab/union_find_network.py \
  --benchmark-series 1000,5000,10000 \
  --benchmark-nodes 1500 \
  --benchmark-seed 7 \
  --output-json projects/union-find-network-lab/sample_benchmark_report.json \
  --output-csv projects/union-find-network-lab/sample_benchmark_report.csv \
  --output-chart projects/union-find-network-lab/sample_benchmark_report.svg
```

Use this when you want committed benchmark artifacts for README charts, blog posts, or project demos.

### CSV-import growth chart export
```bash
python3 projects/union-find-network-lab/union_find_network.py \
  --edges-csv projects/union-find-network-lab/sample_edges.csv \
  --snapshot-every 2 \
  --output-chart projects/union-find-network-lab/sample_component_growth.svg
```

This renders a standalone SVG showing how the largest component grows as more CSV edges are processed.

### Compare union-find against full recomputation
```bash
python3 projects/union-find-network-lab/union_find_network.py \
  --compare-recompute \
  --benchmark-nodes 1500 \
  --benchmark-edges 10000 \
  --benchmark-seed 7 \
  --comparison-checkpoint-every 1250 \
  --output-json projects/union-find-network-lab/sample_recompute_comparison.json \
  --output-chart projects/union-find-network-lab/sample_recompute_comparison.svg
```

This replays the same random edges through union-find and a full BFS component recomputation after every edge, then emits a comparison artifact plus an interview-ready chart.

### Render a chart from an existing artifact
```bash
python3 projects/union-find-network-lab/union_find_network.py \
  --chart-input projects/union-find-network-lab/sample_benchmark_report.csv \
  --output-chart /tmp/union_find_chart.svg \
  --chart-title "Portfolio benchmark throughput"
```

Use this to regenerate charts from checked-in artifacts without rerunning the benchmark itself.

### Export a Markdown portfolio summary from the comparison artifact
```bash
python3 projects/union-find-network-lab/union_find_network.py \
  --chart-input projects/union-find-network-lab/sample_recompute_comparison.json \
  --output-markdown /tmp/union_find_comparison_summary.md
```

Use this when you want an interview-ready README/blog snippet generated directly from the checked-in comparison artifact.

## Sample artifacts
- `projects/union-find-network-lab/sample_benchmark_report.json`
- `projects/union-find-network-lab/sample_benchmark_report.csv`
- `projects/union-find-network-lab/sample_benchmark_report.svg`
- `projects/union-find-network-lab/sample_component_growth.svg`
- `projects/union-find-network-lab/sample_recompute_comparison.json`
- `projects/union-find-network-lab/sample_recompute_comparison.svg`
- `projects/union-find-network-lab/sample_recompute_summary.md`

These are intentionally small, reproducible outputs generated by the CLI so future runs can be compared against a stable baseline.

## Test
```bash
python3 -m unittest projects/union-find-network-lab/test_union_find_network.py
```

## Interview talking points
- explain why union-find beats repeated BFS/DFS recomputation for dynamic connectivity updates
- show how cycle detection falls out naturally when an edge joins nodes already in the same component
- demo the CSV importer as a stepping stone from toy examples to infrastructure/social-network datasets
- mention the seeded benchmark-series export as a reproducible way to create charts and compare future optimizations
- use the recomputation comparison artifact to explain why DSU wins for incremental connectivity workloads while still matching final connectivity outcomes
- show the generated Markdown summary as a lightweight bridge from raw benchmark artifact to README/blog prose
- point out that the SVG exporter is dependency-light and suitable for static portfolio sites or README image generation in CI

## Future improvements
- add dual-axis or multi-series charts so benchmark throughput and component-count trends can be compared in one artifact
- add a tiny README embedding script that refreshes chart references automatically after benchmark runs

# consistent-hashing-lab

A distributed-systems portfolio project that simulates a consistent hashing ring with virtual nodes and replication-aware placement.

## Why it is interesting
- Demonstrates a real systems concept used in caches, databases, and sharded services.
- Shows deterministic hashing, load distribution analysis, topology-change remapping, and multi-replica placement.
- Produces JSON reports that are easy to inspect, script, or screenshot for a portfolio.

## Features
- reusable consistent hash ring implementation
- configurable virtual node count
- deterministic primary-owner assignment to physical nodes
- replication-factor support with distinct physical-node selection
- distribution/load report for generated key sets
- effective replication reporting when requested replicas exceed available nodes
- node add/remove remap simulation with movement ratio and replica-placement change output
- virtual-node benchmark mode that compares imbalance and optional remap behavior across multiple ring sizes
- chart-ready CSV export and recruiter-friendly Markdown export for benchmark series
- self-contained SVG and HTML ring visualizations with sample key ownership overlays

## Usage

Assign explicit keys to primary owners:

```bash
python3 consistent_hashing.py assign \
  --nodes node-a node-b node-c \
  --keys user:1 user:2 user:3 \
  --virtual-nodes 128
```

Assign explicit keys with replica sets:

```bash
python3 consistent_hashing.py assign \
  --nodes node-a node-b node-c node-d \
  --keys user:1 user:2 user:3 \
  --virtual-nodes 128 \
  --replication-factor 2
```

Inspect replication-aware load distribution:

```bash
python3 consistent_hashing.py report \
  --nodes node-a node-b node-c node-d \
  --key-count 5000 \
  --virtual-nodes 128 \
  --replication-factor 2
```

Simulate adding a node:

```bash
python3 consistent_hashing.py remap \
  --nodes node-a node-b node-c \
  --key-count 5000 \
  --virtual-nodes 128 \
  --add-node node-d
```

Simulate how replicated placement changes after a node joins:

```bash
python3 consistent_hashing.py remap \
  --nodes node-a node-b node-c \
  --key-count 5000 \
  --virtual-nodes 128 \
  --replication-factor 2 \
  --add-node node-d
```

Benchmark several virtual-node counts to see how they affect balance:

```bash
python3 consistent_hashing.py benchmark \
  --nodes node-a node-b node-c node-d \
  --key-count 5000 \
  --virtual-node-counts 1 8 32 128 512
```

Benchmark virtual-node counts while also measuring how many keys move when a node joins:

```bash
python3 consistent_hashing.py benchmark \
  --nodes node-a node-b node-c \
  --key-count 5000 \
  --virtual-node-counts 1 8 32 128 \
  --add-node node-d
```

Write the same benchmark series to chart-ready CSV and a portfolio-friendly Markdown report:

```bash
python3 consistent_hashing.py benchmark \
  --nodes node-a node-b node-c \
  --key-count 5000 \
  --virtual-node-counts 1 8 32 128 \
  --replication-factor 2 \
  --add-node node-d \
  --csv-out docs/artifacts/consistent-hashing-lab/sample-virtual-node-benchmark.csv \
  --markdown-out docs/artifacts/consistent-hashing-lab/sample-virtual-node-benchmark.md
```

Render a portfolio-ready ring snapshot with sample key ownership and load bars:

```bash
python3 consistent_hashing.py visualize \
  --nodes node-a node-b node-c node-d \
  --key-count 24 \
  --displayed-key-count 12 \
  --virtual-nodes 32 \
  --replication-factor 2 \
  --title "Consistent hashing ring with replica placement" \
  --svg-out docs/artifacts/consistent-hashing-lab/sample-ring-visualization.svg \
  --html-out docs/artifacts/consistent-hashing-lab/sample-ring-visualization.html
```

## Notes
- Replica selection always returns distinct physical nodes.
- If `--replication-factor` is larger than the number of physical nodes, the report exposes the capped `effective_replication_factor`.
- `benchmark` returns `best_imbalance_virtual_nodes` so the most balanced tested ring size is easy to spot in screenshots or follow-up exports.
- `benchmark` accepts either `--add-node` or `--remove-node` when you want movement metrics, but not both in the same run.
- `--csv-out` flattens the benchmark series into spreadsheet-friendly rows, including the tested topology change and the best imbalance point.
- `--markdown-out` renders the same deterministic series as a concise benchmark report with a summary table and takeaways.
- `visualize` keeps stdout as a concise JSON summary while `--svg-out` and `--html-out` write screenshot-friendly artifacts.
- `--displayed-key-count` limits how many keys are drawn on the ring so the diagram stays readable even when the load report covers more keys.

## Sample committed artifacts
- `docs/artifacts/consistent-hashing-lab/sample-virtual-node-benchmark.json`
- `docs/artifacts/consistent-hashing-lab/sample-virtual-node-benchmark.csv`
- `docs/artifacts/consistent-hashing-lab/sample-virtual-node-benchmark.md`
- `docs/artifacts/consistent-hashing-lab/sample-ring-visualization.json`
- `docs/artifacts/consistent-hashing-lab/sample-ring-visualization.svg`
- `docs/artifacts/consistent-hashing-lab/sample-ring-visualization.html`

## Test

```bash
python3 -m unittest projects/consistent-hashing-lab/test_consistent_hashing.py
```

## Future improvements
- simulate rack/zone-aware replica placement constraints
- add PNG capture or multi-topology galleries so the ring snapshots are even easier to drop into slides

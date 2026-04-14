# consistent-hashing-lab

A distributed-systems portfolio project that simulates a consistent hashing ring with virtual nodes.

## Why it is interesting
- Demonstrates a real systems concept used in caches, databases, and sharded services.
- Shows deterministic hashing, load distribution analysis, and topology-change remapping.
- Produces JSON reports that are easy to inspect, script, or screenshot for a portfolio.

## Features
- reusable consistent hash ring implementation
- configurable virtual node count
- deterministic key assignment to physical nodes
- distribution/load report for generated key sets
- node add/remove remap simulation with movement ratio output

## Usage

Assign explicit keys:

```bash
python3 consistent_hashing.py assign \
  --nodes node-a node-b node-c \
  --keys user:1 user:2 user:3 \
  --virtual-nodes 128
```

Inspect load distribution:

```bash
python3 consistent_hashing.py report \
  --nodes node-a node-b node-c \
  --key-count 5000 \
  --virtual-nodes 128
```

Simulate adding a node:

```bash
python3 consistent_hashing.py remap \
  --nodes node-a node-b node-c \
  --key-count 5000 \
  --virtual-nodes 128 \
  --add-node node-d
```

## Test

```bash
python3 -m unittest projects/consistent-hashing-lab/test_consistent_hashing.py
```

## Future improvements
- add replication-factor support with distinct-node selection
- render the ring visually for before/after topology screenshots
- benchmark how virtual node counts change imbalance and movement ratios

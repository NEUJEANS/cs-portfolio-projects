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

## Notes
- Replica selection always returns distinct physical nodes.
- If `--replication-factor` is larger than the number of physical nodes, the report exposes the capped `effective_replication_factor`.

## Test

```bash
python3 -m unittest projects/consistent-hashing-lab/test_consistent_hashing.py
```

## Future improvements
- render the ring visually for before/after topology screenshots
- benchmark how virtual node counts change imbalance and movement ratios
- simulate rack/zone-aware replica placement constraints

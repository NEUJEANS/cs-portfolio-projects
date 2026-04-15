# chord-dht-lab

A portfolio-friendly distributed-systems lab that simulates a Chord distributed hash table, explains finger tables, and traces key lookups across the ring.

## Why it is interesting
- demonstrates a classic peer-to-peer indexing design built on consistent hashing
- shows how logarithmic routing emerges from finger tables instead of linear scans
- produces interview-ready artifacts: node IDs, finger tables, key placement, lookup hop traces, and benchmark summaries
- makes node joins tangible by previewing which keys move after rebalancing

## Features
- deterministic SHA-1-based identifier mapping into an `m`-bit ring
- node successor/predecessor logic and full finger-table generation
- traced key lookup from a chosen start node to the responsible owner
- linear-successor baseline lookup for side-by-side hop-count comparison
- key assignment report plus join preview showing moved keys
- benchmark mode that summarizes hop savings across keys and start nodes
- JSON ring input for reproducible demos and unit tests

## Usage

Print the bundled demo payload:

```bash
python3 projects/chord-dht-lab/chord_dht.py demo --pretty
```

Trace a lookup through a custom ring:

```bash
python3 projects/chord-dht-lab/chord_dht.py route projects/chord-dht-lab/ring.json alpha compiler --pretty
```

Preview which keys move when a node joins:

```bash
python3 projects/chord-dht-lab/chord_dht.py join projects/chord-dht-lab/ring.json foxtrot report.pdf slides compiler --pretty
```

Compare finger-table routing against naive successor forwarding:

```bash
python3 projects/chord-dht-lab/chord_dht.py benchmark \
  projects/chord-dht-lab/ring.json \
  compiler slides final-project \
  --start-node alpha \
  --start-node charlie \
  --pretty
```

Ring format:

```json
{
  "m_bits": 8,
  "nodes": ["alpha", "bravo", "charlie", "delta", "echo"]
}
```

## Test

```bash
python3 -m unittest tests/test_chord_dht_lab.py
```

## Design notes
- Keys are assigned to the first node whose ID is greater than or equal to the key ID, wrapping at the end of the ring.
- Each finger entry for node `n` starts at `n + 2^i mod 2^m`, and points to the successor of that start identifier.
- The lookup implementation routes with the closest preceding finger when possible, then falls back to the immediate successor.
- The benchmark uses the same ring and key identifiers for both lookup strategies so hop-count differences stay attributable to routing logic rather than input drift.
- This lab models the core routing/data-placement ideas cleanly, without adding unstable background maintenance or failure recovery.

## Future improvements
- add stabilization/successor-list simulation for churn scenarios
- export the ring and lookup routes as Graphviz diagrams
- generate larger synthetic rings and workloads directly from the CLI for broader benchmarking

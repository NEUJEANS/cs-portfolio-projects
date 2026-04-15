# chord-dht-lab

A portfolio-friendly distributed-systems lab that simulates a Chord distributed hash table, explains finger tables, and traces key lookups across the ring.

## Why it is interesting
- demonstrates a classic peer-to-peer indexing design built on consistent hashing
- shows how logarithmic routing emerges from finger tables instead of linear scans
- produces interview-ready artifacts: node IDs, finger tables, successor lists, key placement, lookup hop traces, stabilization rounds, and benchmark summaries
- makes node joins and replica-based failover tangible instead of leaving fault tolerance as a hand-wavy follow-up

## Features
- deterministic SHA-1-based identifier mapping into an `m`-bit ring
- node successor/predecessor logic, successor lists, and full finger-table generation
- traced key lookup from a chosen start node to the responsible owner
- linear-successor baseline lookup for side-by-side hop-count comparison
- key assignment report plus join preview showing moved keys
- successor-list replica planning and failure simulation for degraded/unavailable key checks
- explicit stabilization-round simulation for join/failure repair of successor, predecessor, and finger metadata
- configurable `fix_fingers` scheduling modes so stabilization can model one-slot, full-round, or seeded-random finger repair policies
- side-by-side stabilization comparison mode so multiple repair schedules can be evaluated on the same join/failure scenario
- Markdown/CSV export for stabilization comparison summaries so portfolio write-ups can reuse the results directly
- churn workload driver that chains joins/failures and summarizes stabilization step-by-step
- Graphviz DOT export for the base ring, traced lookup routes, and stabilization progression diagrams
- benchmark mode that summarizes hop savings across keys and start nodes
- deterministic synthetic ring/workload generation for broader benchmark experiments without hand-writing JSON
- optional seeded random sampling of benchmark start nodes so larger rings can be profiled without always biasing toward the first sorted nodes
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

Generate a larger deterministic synthetic ring and workload for benchmark experiments:

```bash
python3 projects/chord-dht-lab/chord_dht.py synth-benchmark \
  --m-bits 10 \
  --nodes 16 \
  --keys 32 \
  --seed 7 \
  --start-nodes 4 \
  --pretty
```

Sample a seeded random subset of start nodes instead of always using the first sorted nodes:

```bash
python3 projects/chord-dht-lab/chord_dht.py synth-benchmark \
  --m-bits 10 \
  --nodes 16 \
  --keys 32 \
  --seed 7 \
  --start-nodes 4 \
  --start-node-sample-mode random \
  --start-node-seed 101 \
  --pretty
```

Simulate successor-list failover during node outages:

```bash
python3 projects/chord-dht-lab/chord_dht.py resilience \
  projects/chord-dht-lab/ring.json \
  compiler slides final-project \
  --failed-node alpha \
  --failed-node echo \
  --replica-count 3 \
  --pretty
```

Simulate stabilization rounds after a join:

```bash
python3 projects/chord-dht-lab/chord_dht.py stabilize \
  projects/chord-dht-lab/ring.json \
  --joined-node foxtrot \
  --rounds 8 \
  --finger-repair-mode single \
  --pretty
```

Simulate stabilization after a failure:

```bash
python3 projects/chord-dht-lab/chord_dht.py stabilize \
  projects/chord-dht-lab/ring.json \
  --failed-node echo \
  --rounds 8 \
  --pretty
```

Compare alternative `fix_fingers` repair schedules on the same scenario:

```bash
python3 projects/chord-dht-lab/chord_dht.py compare-stabilize \
  projects/chord-dht-lab/ring.json \
  --joined-node foxtrot \
  --rounds 4 \
  --mode single \
  --mode all \
  --mode random \
  --random-seed 17 \
  --pretty
```

Export a stabilization comparison summary as Markdown for portfolio notes:

```bash
python3 projects/chord-dht-lab/chord_dht.py compare-stabilize-export \
  projects/chord-dht-lab/ring.json \
  --joined-node foxtrot \
  --rounds 4
```

Export the same summary as CSV for charts or spreadsheets:

```bash
python3 projects/chord-dht-lab/chord_dht.py compare-stabilize-export \
  projects/chord-dht-lab/ring.json \
  --joined-node foxtrot \
  --rounds 4 \
  --format csv
```

Compare alternative `fix_fingers` repair schedules:

```bash
python3 projects/chord-dht-lab/chord_dht.py stabilize \
  projects/chord-dht-lab/ring.json \
  --joined-node foxtrot \
  --rounds 3 \
  --finger-repair-mode all \
  --pretty

python3 projects/chord-dht-lab/chord_dht.py stabilize \
  projects/chord-dht-lab/ring.json \
  --joined-node foxtrot \
  --rounds 4 \
  --finger-repair-mode random \
  --finger-repair-seed 17 \
  --pretty
```

Run a resumable churn scenario that chains joins and failures:

```bash
python3 projects/chord-dht-lab/chord_dht.py churn \
  projects/chord-dht-lab/ring.json \
  projects/chord-dht-lab/churn_events.json \
  --finger-repair-mode all \
  --pretty
```

Event file format:

```json
[
  {"action": "join", "node": "foxtrot", "rounds": 4},
  {"action": "fail", "node": "charlie", "rounds": 3}
]
```

Export a Graphviz DOT diagram for a lookup route:

```bash
python3 projects/chord-dht-lab/chord_dht.py graphviz \
  projects/chord-dht-lab/ring.json \
  --mode route \
  --start-node alpha \
  --key compiler
```

Export a stabilization progression diagram:

```bash
python3 projects/chord-dht-lab/chord_dht.py graphviz \
  projects/chord-dht-lab/ring.json \
  --mode stabilize \
  --joined-node foxtrot \
  --rounds 4 \
  --finger-repair-mode random \
  --finger-repair-seed 17
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
- A successor list is the next few clockwise nodes after a given node; in production Chord systems it helps recovery when a primary successor fails.
- The lookup implementation routes with the closest preceding finger when possible, then falls back to the immediate successor.
- The resilience command models simple successor-replica failover: the primary owner is first, then consecutive successors act as backups.
- The stabilize command starts from stale metadata after a join or failure event, repairs successor/predecessor links every round, and can repair one finger slot in order, one seeded-random slot (seed required for reproducibility), or all finger slots per round.
- The graphviz command emits plain DOT text so diagrams can be rendered with Graphviz locally or pasted into online DOT viewers.
- The benchmark uses the same ring and key identifiers for both lookup strategies so hop-count differences stay attributable to routing logic rather than input drift.

## Future improvements
- compare benchmark summaries across multiple random start-node samples to show variance instead of a single seeded subset
- export benchmark summaries as CSV/Markdown tables for portfolio write-ups
- model recovery under node recovery/rejoin events in addition to joins/failures

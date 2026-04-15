# Distributed Snapshot Lab

A small distributed-systems simulation that demonstrates the Chandy-Lamport distributed snapshot algorithm on a bank-transfer network with in-flight messages.

## Why this project is portfolio-worthy
- turns a classic distributed-systems paper into a runnable, testable program
- shows how consistent cuts can include in-transit messages instead of only local balances
- gives you concrete interview material for markers, channel state, stable properties, and global-state debugging
- exports Mermaid sequence diagrams so the execution is easy to present in a README, blog post, or interview follow-up
- now supports named concurrent snapshots, which makes the lab feel closer to real distributed debugging tooling
- stays small enough to understand end to end while still feeling like a real systems lab

## Features
- process-local balances plus directed channels with queued in-flight transfers
- transfer and delivery simulation that preserves total money across local state and channels
- snapshot capture initiated by any process
- marker-delay controls to model different channel recording windows
- named concurrent snapshots with isolated results per snapshot ID
- JSON CLI output that is easy to inspect or feed into follow-up tooling
- Mermaid sequence-diagram export for presentation-ready visualization
- unit and CLI tests for core invariants and representative scenarios

## Project structure
- `distributed_snapshot_lab.py` - simulation model and CLI
- `test_distributed_snapshot_lab.py` - unit + CLI tests

## Usage
Run from this directory.

### Capture a snapshot with an in-flight message recorded on one incoming channel
```bash
python3 distributed_snapshot_lab.py simulate \
  --balances '{"A": 10, "B": 10, "C": 10}' \
  --send A:B:3:ab-1 \
  --send C:B:2:cb-1 \
  --snapshot A \
  --marker-delay 'A->B=0' \
  --marker-delay 'C->B=2'
```

### Export the same run as a Mermaid sequence diagram
```bash
python3 distributed_snapshot_lab.py simulate \
  --balances '{"A": 10, "B": 10, "C": 10}' \
  --send A:B:3:ab-1 \
  --send C:B:2:cb-1 \
  --snapshot A \
  --marker-delay 'A->B=0' \
  --marker-delay 'C->B=2' \
  --output mermaid
```

### Capture two concurrent snapshots over the same execution
```bash
python3 distributed_snapshot_lab.py concurrent \
  --balances '{"A": 10, "B": 10, "C": 10}' \
  --send A:B:3:ab-1 \
  --send C:B:2:cb-1 \
  --snapshot blue:A \
  --snapshot green:C \
  --marker-delay 'blue:A->B=0' \
  --marker-delay 'blue:C->B=2' \
  --marker-delay 'green:C->B=0' \
  --marker-delay 'green:A->B=2'
```

### Deliver a transfer before taking the snapshot
```bash
python3 distributed_snapshot_lab.py simulate \
  --balances '{"A": 12, "B": 8}' \
  --send A:B:4:salary \
  --deliver A:B \
  --snapshot A
```

## Testing
```bash
python3 -m unittest discover -s projects/distributed-snapshot-lab -p 'test_*.py' -v
```

## Interview talking points
- why a globally consistent state is not the same as sampling every process at exactly the same wall-clock time
- how marker messages bound which incoming-channel messages count as part of the snapshot
- why stable predicates and debugging tools care about consistent cuts
- how total-money invariants help sanity-check the implementation
- how concurrent snapshot IDs prevent one in-progress observation from polluting another
- why lightweight visualization export makes distributed behavior easier to explain than raw JSON alone

## Future improvements
- add scripted failure/recovery scenarios alongside normal transfers
- export richer Mermaid notes for per-process recorded state transitions
- generate markdown-ready assets automatically for project pages

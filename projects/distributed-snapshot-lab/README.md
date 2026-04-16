# Distributed Snapshot Lab

A small distributed-systems simulation that demonstrates the Chandy-Lamport distributed snapshot algorithm on a bank-transfer network with in-flight messages.

## Why this project is portfolio-worthy
- turns a classic distributed-systems paper into a runnable, testable program
- shows how consistent cuts can include in-transit messages instead of only local balances
- gives you concrete interview material for markers, channel state, stable properties, and global-state debugging
- exports Mermaid sequence diagrams so the execution is easy to present in a README, blog post, or interview follow-up
- supports named concurrent snapshots and scripted failure/recovery scenarios, so the lab feels closer to real distributed debugging tooling
- stays small enough to understand end to end while still feeling like a real systems lab

## Features
- process-local balances plus directed channels with queued in-flight transfers
- transfer and delivery simulation that preserves total money across local state and channels
- process up/down state for lightweight crash/recovery scenarios
- directed link up/down state to model one-way network partitions separately from whole-process failures
- snapshot capture initiated by any live process
- marker-delay controls to model different channel recording windows
- named concurrent snapshots with isolated results per snapshot ID
- scripted scenario playback with `send`, `deliver`, `fail`, `recover`, `link-fail`, `link-recover`, and `snapshot` steps
- JSON CLI output that is easy to inspect or feed into follow-up tooling
- Mermaid sequence-diagram export for presentation-ready visualization, including fail/recover notes
- Markdown walkthrough export for scripted partition-heal case studies with embedded Mermaid diagrams
- direct SVG walkthrough asset export for project pages, slide decks, and README embeds
- optional PNG walkthrough asset export via headless-browser screenshots of the generated SVGs
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

### Model a simple outage before snapshot capture
```bash
python3 distributed_snapshot_lab.py simulate \
  --balances '{"A": 10, "B": 10, "C": 10}' \
  --send A:B:3:ab-1 \
  --fail C \
  --snapshot A
```

### Snapshot during a one-way link partition
```bash
python3 distributed_snapshot_lab.py simulate \
  --balances '{"A": 10, "B": 10, "C": 10}' \
  --send C:B:2:cb-1 \
  --link-fail A:B \
  --snapshot A \
  --marker-delay 'C->B=2'
```

### Replay a scripted failure/recovery scenario
```bash
python3 distributed_snapshot_lab.py script \
  --balances '{"A": 10, "B": 10, "C": 10}' \
  --marker-delay 'C->B=2' \
  --script '[
    {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
    {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
    {"op": "fail", "process": "B", "reason": "reboot"},
    {"op": "snapshot", "snapshot_id": "during-outage", "initiator": "A"},
    {"op": "recover", "process": "B"},
    {"op": "deliver", "sender": "A", "receiver": "B"},
    {"op": "deliver", "sender": "C", "receiver": "B"},
    {"op": "snapshot", "snapshot_id": "after-recovery", "initiator": "A"}
  ]'
```

### Generate a Markdown partition-heal walkthrough asset plus SVG/PNG slide-deck exports
```bash
python3 distributed_snapshot_lab.py walkthrough \
  --balances '{"A": 10, "B": 10, "C": 10}' \
  --marker-delay 'C->B=2' \
  --title 'Distributed Snapshot Partition-Heal Walkthrough' \
  --output ../../docs/artifacts/distributed-snapshot-partition-heal-walkthrough.md \
  --svg-dir ../../docs/artifacts/distributed-snapshot-partition-heal-svg \
  --svg-prefix distributed-snapshot-partition-heal \
  --png-dir ../../docs/artifacts/distributed-snapshot-partition-heal-png \
  --png-prefix distributed-snapshot-partition-heal \
  --script '[
    {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
    {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
    {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "uplink partition"},
    {"op": "snapshot", "snapshot_id": "during-partition", "initiator": "A"},
    {"op": "link-recover", "sender": "A", "receiver": "B", "reason": "healed"},
    {"op": "deliver", "sender": "A", "receiver": "B"},
    {"op": "deliver", "sender": "C", "receiver": "B"},
    {"op": "snapshot", "snapshot_id": "after-heal", "initiator": "A"}
  ]'
```
The repository ships one generated walkthrough at `docs/artifacts/distributed-snapshot-partition-heal-walkthrough.md`, reusable SVG assets under `docs/artifacts/distributed-snapshot-partition-heal-svg/`, and presentation-friendly PNG assets under `docs/artifacts/distributed-snapshot-partition-heal-png/`.

## Output notes
- `process_statuses` reports which processes were `up` or `down` when the snapshot was recorded.
- `channel_statuses` reports which directed links were `up` or `down`, so a partitioned edge is visible in both JSON and Mermaid output.
- failed receivers block `deliver` until they recover, so queued channel state can survive across an outage.
- failed or partitioned directed links block both new sends and deliveries on that edge until recovery.
- failed processes cannot send new transfers or initiate snapshots in this lightweight model.
- scripted runs return the final balances, remaining in-flight messages, full timeline, and every snapshot captured during the script.
- `walkthrough` turns a scripted scenario into Markdown with step summaries plus one Mermaid diagram per snapshot, and can also emit one SVG asset per snapshot for reusable documentation/slide embeds.
- PNG export is optional, keeps SVG as the canonical source, and currently requires `google-chrome`, `google-chrome-stable`, `chromium`, or `chromium-browser` on `PATH` when `--png-dir` is used.

## Testing
```bash
python3 -m unittest -v test_distributed_snapshot_lab.py
```

## Interview talking points
- why a globally consistent state is not the same as sampling every process at exactly the same wall-clock time
- how marker messages bound which incoming-channel messages count as part of the snapshot
- why stable predicates and debugging tools care about consistent cuts
- how total-money invariants help sanity-check the implementation
- how concurrent snapshot IDs prevent one in-progress observation from polluting another
- how lightweight crash/recovery scripting reveals the difference between local liveness and global money conservation
- why visualization export makes distributed behavior easier to explain than raw JSON alone

## Future improvements
- export richer Mermaid notes for per-process recorded state transitions
- generate a single-page HTML or PDF handout that bundles the walkthrough narrative with the committed SVG/PNG assets
- generate markdown-ready assets automatically for additional project pages

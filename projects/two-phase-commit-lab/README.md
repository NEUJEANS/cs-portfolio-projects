# Two-Phase Commit Lab

A compact Python simulator that turns the classic distributed-transaction 2PC protocol into runnable portfolio artifacts. It shows the happy path, participant-driven aborts, coordinator crash blocking, coordinator recovery from a durable decision log, participant-side reconnect recovery after missed second-phase messages, and peer-assisted termination hints for coordinator-unavailable incidents without requiring a real database cluster.

## Why this project is portfolio-worthy
- demonstrates distributed-systems fundamentals beyond consensus by modeling atomic commit across multiple services
- gives you concrete recruiter/interview examples for `PREPARE`, durable decision logs, blocking behavior, coordinator replay, participant reconnect recovery, and peer-to-peer termination checks
- stays dependency-free and readable while still producing artifact-friendly Markdown reports for GitHub browsing
- complements the repo's Raft, Chord, CRDT, and routing labs with transactional coordination instead of replication or routing logic

## Features
- JSON scenario validation for participant plans, votes, second-phase delivery quirks, coordinator crash/recovery settings, and optional pre-crash decision-delivery counts
- deterministic 2PC simulation with trace output for `PREPARE`, votes, durable decisions, crash points, partial second-phase delivery, missed second-phase deliveries, and participant reconnect recovery
- blocked-case termination hints that explain what a prepared participant can still ask peers while the coordinator is unavailable
- committed sample scenarios for happy-path commit, participant veto abort, coordinator blocking before the decision log, durable-decision replay after a crash, one-peer-visible `COMMIT` after a crash, and participant-side reconnect after a missed `COMMIT`
- Markdown report export for recruiter-friendly artifacts under `docs/artifacts/two-phase-commit-lab/`
- multi-scenario catalog generation that regenerates per-scenario reports and writes a portfolio-friendly landing page comparing outcomes, reconnect recoveries, and termination hints in one place
- clean CLI commands for validation, single-scenario simulation, and bundle generation

## Project structure
- `two_phase_commit_lab.py` - validator, simulator, report renderer, catalog generator, and CLI entrypoint
- `order_success.json` - all participants vote YES and the transaction commits
- `payment_validation_abort.json` - one participant votes NO so the transaction aborts globally
- `coordinator_crash_before_decision.json` - all participants prepare, but the coordinator crashes before a durable outcome exists
- `coordinator_crash_partial_commit_delivery.json` - the coordinator logs COMMIT, one participant hears it, then the coordinator crashes while other prepared peers remain blocked
- `coordinator_recovery_commit.json` - the coordinator logs COMMIT, crashes, then replays the decision during recovery
- `participant_reconnect_commit.json` - a prepared participant misses the first `COMMIT`, reconnects, and resolves the durable outcome safely
- `CHECKLIST.md` - resumable slice history plus next ideas
- `tests/test_two_phase_commit_lab.py` - regression tests for validation, simulation, CLI output, and catalog generation
- `docs/artifacts/two-phase-commit-lab/` - committed per-scenario reports plus the scenario catalog landing page

## Scenario format
```json
{
  "title": "Order service happy-path commit",
  "description": "Inventory, billing, and shipping all vote YES.",
  "transaction_id": "order-1042",
  "participants": [
    {"name": "inventory", "role": "reserve stock", "vote": "commit"},
    {
      "name": "billing",
      "role": "capture payment",
      "vote": "commit",
      "second_phase_delivery": "miss",
      "reconnect_after_missed_decision": true
    }
  ],
  "failures": {
    "coordinator_crash": "after-decision-log",
    "recover_after_crash": false,
    "decision_deliveries_before_crash": 1
  }
}
```

### Supported votes
- `commit` - participant writes a local prepared record and replies YES
- `abort` - participant replies NO, forcing a global abort
- `timeout` - participant never responds within the coordinator timeout window, also forcing a global abort

### Supported second-phase delivery behaviors
- `deliver` - default; the participant receives the first `COMMIT`/`ABORT` broadcast normally
- `miss` - the participant prepared successfully but misses the first second-phase message and stays in doubt until a retry, recovery, or reconnect resolves it

If `reconnect_after_missed_decision` is `true`, the prepared participant later reconnects, asks for the durable decision, and finishes phase two without changing the global outcome.

### Supported coordinator crash points
- `none` - normal flow
- `before-decision` - crash after all YES votes are collected but before a durable decision is recorded
- `after-decision-log` - crash after COMMIT/ABORT is durable but before every participant hears it

If `recover_after_crash` is `true`, the simulator runs a recovery step:
- after `before-decision`, recovery cannot prove a durable COMMIT record, so the safe choice is ABORT
- after `after-decision-log`, recovery replays the durable decision and completes phase two

If `decision_deliveries_before_crash` is greater than `0`, the simulator lets that many prepared participants hear the durable decision before the coordinator crashes, which is useful for demonstrating peer-visible termination hints in blocked incidents.

## Usage
Run from the repository root.

### Validate a scenario
```bash
python3 projects/two-phase-commit-lab/two_phase_commit_lab.py validate \
  projects/two-phase-commit-lab/order_success.json
```

### Run a scenario summary
```bash
python3 projects/two-phase-commit-lab/two_phase_commit_lab.py run \
  projects/two-phase-commit-lab/payment_validation_abort.json
```

### Emit the full JSON result
```bash
python3 projects/two-phase-commit-lab/two_phase_commit_lab.py run \
  projects/two-phase-commit-lab/coordinator_recovery_commit.json \
  --json
```

### Export a Markdown artifact report
```bash
python3 projects/two-phase-commit-lab/two_phase_commit_lab.py run \
  projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json \
  --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_report.md
```

### Generate the multi-scenario catalog bundle
```bash
python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog \
  projects/two-phase-commit-lab \
  --markdown-out docs/artifacts/two-phase-commit-lab/scenario_catalog.md \
  --report-dir docs/artifacts/two-phase-commit-lab
```

## What the committed samples show
- `order_success.json`
  - every participant writes a prepared record, the coordinator logs COMMIT, and the second phase finishes cleanly
- `payment_validation_abort.json`
  - one service can veto the distributed transaction, proving that prepared peers must roll back instead of committing alone
- `coordinator_crash_before_decision.json`
  - plain 2PC can block when all participants are prepared but the coordinator crashes before a durable outcome exists
- `coordinator_crash_partial_commit_delivery.json`
  - blocked does not always mean pure darkness: one participant already knows COMMIT, so peers can use a termination check to learn what the coordinator had durably decided
- `coordinator_recovery_commit.json`
  - once the decision log is durable, recovery can safely replay COMMIT and finish the protocol after a crash
- `participant_reconnect_commit.json`
  - a prepared participant can still end up temporarily in doubt after missing the first second-phase message, then safely finish by reconnecting to learn the durable decision
- `scenario_catalog.md`
  - one landing page compares all committed scenarios so recruiters can browse the protocol story without opening each artifact separately

## Testing
```bash
python3 -m unittest tests.test_two_phase_commit_lab -v
```

## Future ideas
- add a side-by-side 2PC vs 3PC comparison mode to explain why non-blocking atomic commit is harder
- add scenario tags or thematic groupings (happy path, blocking, coordinator recovery, participant reconnect, peer hints) inside the catalog if the sample set grows larger
- optionally simulate full peer-to-peer termination resolution once a blocked participant reaches a decisive peer

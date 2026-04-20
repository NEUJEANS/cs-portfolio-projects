# Two-Phase Commit Lab

A compact Python simulator that turns the classic distributed-transaction 2PC protocol into runnable portfolio artifacts. It shows the happy path, participant-driven aborts, coordinator crash blocking, and coordinator recovery from a durable decision log without requiring a real database cluster.

## Why this project is portfolio-worthy
- demonstrates distributed-systems fundamentals beyond consensus by modeling atomic commit across multiple services
- gives you concrete recruiter/interview examples for `PREPARE`, durable decision logs, blocking behavior, and recovery replay
- stays dependency-free and readable while still producing artifact-friendly Markdown reports for GitHub browsing
- complements the repo's Raft, Chord, CRDT, and routing labs with transactional coordination instead of replication or routing logic

## Features
- JSON scenario validation for participant plans, votes, and coordinator crash/recovery settings
- deterministic 2PC simulation with trace output for `PREPARE`, votes, durable decisions, crash points, and second-phase delivery
- committed sample scenarios for happy-path commit, participant veto abort, coordinator blocking before the decision log, and recovery after a durable commit
- Markdown report export for recruiter-friendly artifacts under `docs/artifacts/two-phase-commit-lab/`
- multi-scenario catalog generation that regenerates per-scenario reports and writes a portfolio-friendly landing page comparing outcomes in one place
- clean CLI commands for validation, single-scenario simulation, and bundle generation

## Project structure
- `two_phase_commit_lab.py` - validator, simulator, single-report renderer, catalog generator, and CLI entrypoint
- `order_success.json` - all participants vote YES and the transaction commits
- `payment_validation_abort.json` - one participant votes NO so the transaction aborts globally
- `coordinator_crash_before_decision.json` - all participants prepare, but the coordinator crashes before a durable decision exists
- `coordinator_recovery_commit.json` - the coordinator logs COMMIT, crashes, then replays the decision during recovery
- `CHECKLIST.md` - resumable slice history plus next ideas
- `tests/test_two_phase_commit_lab.py` - regression tests for validation, simulation, and CLI artifact output
- `docs/artifacts/two-phase-commit-lab/` - committed per-scenario reports plus the scenario catalog landing page

## Scenario format
```json
{
  "title": "Order service happy-path commit",
  "description": "Inventory, billing, and shipping all vote YES.",
  "transaction_id": "order-1042",
  "participants": [
    {"name": "inventory", "role": "reserve stock", "vote": "commit"},
    {"name": "billing", "role": "capture payment", "vote": "commit"}
  ],
  "failures": {
    "coordinator_crash": "none",
    "recover_after_crash": false
  }
}
```

### Supported votes
- `commit` - participant writes a local prepared record and replies YES
- `abort` - participant replies NO, forcing a global abort
- `timeout` - participant never responds within the coordinator timeout window, also forcing a global abort

### Supported coordinator crash points
- `none` - normal flow
- `before-decision` - crash after all YES votes are collected but before a durable decision is recorded
- `after-decision-log` - crash after COMMIT/ABORT is durable but before every participant hears it

If `recover_after_crash` is `true`, the simulator runs a recovery step:
- after `before-decision`, recovery cannot prove a durable COMMIT record, so the safe choice is ABORT
- after `after-decision-log`, recovery replays the durable decision and completes phase two

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
  projects/two-phase-commit-lab/coordinator_crash_before_decision.json \
  --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_report.md
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
- `coordinator_recovery_commit.json`
  - once the decision log is durable, recovery can safely replay COMMIT and finish the protocol after a crash
- `scenario_catalog.md`
  - one landing page compares all committed scenarios so recruiters can browse the protocol story without opening each artifact separately

## Testing
```bash
python3 -m unittest tests.test_two_phase_commit_lab -v
```

## Future ideas
- add participant-side recovery behavior for reconnecting after timeouts or missed second-phase messages
- add a side-by-side 2PC vs 3PC comparison mode to explain why non-blocking atomic commit is harder
- add scenario tags or thematic groupings (happy path, blocking, recovery) inside the catalog if the sample set grows larger

# Two-Phase Commit Lab

A compact Python simulator that turns the classic distributed-transaction 2PC protocol into runnable portfolio artifacts. It shows the happy path, participant-driven aborts, coordinator crash blocking, coordinator recovery from a durable decision log, participant-side reconnect recovery after missed second-phase messages, peer-assisted termination hints, and a full peer-to-peer termination-resolution pass for coordinator-unavailable incidents without requiring a real database cluster.

## Why this project is portfolio-worthy
- demonstrates distributed-systems fundamentals beyond consensus by modeling atomic commit across multiple services
- gives you concrete recruiter/interview examples for `PREPARE`, durable decision logs, blocking behavior, coordinator replay, participant reconnect recovery, and peer-to-peer termination checks
- stays dependency-free and readable while still producing artifact-friendly Markdown reports for GitHub browsing
- complements the repo's Raft, Chord, CRDT, and routing labs with transactional coordination instead of replication or routing logic

## Features
- JSON scenario validation for participant plans, votes, second-phase delivery quirks, coordinator crash/recovery settings, and optional pre-crash decision-delivery counts
- deterministic 2PC simulation with trace output for `PREPARE`, votes, durable decisions, crash points, partial second-phase delivery, missed second-phase deliveries, and participant reconnect recovery
- blocked-case termination hints that explain what a prepared participant can still ask peers while the coordinator is unavailable
- peer-to-peer termination-resolution mode that actually plays out what happens when a blocked participant reaches a decisive peer (or proves that everyone is still stuck)
- committed sample scenarios for happy-path commit, participant veto abort, coordinator blocking before the decision log, durable-decision replay after a crash, one-peer-visible `COMMIT` after a crash, blocked-after-`ABORT` resolution via a non-prepared peer, and participant-side reconnect after a missed `COMMIT`
- protocol comparison mode that contrasts the same business incident as plain 2PC versus an orchestrated saga, making the blocking-vs-compensation trade-off visible in Markdown, JSON, and static HTML dashboard artifacts
- Markdown report export for recruiter-friendly artifacts under `docs/artifacts/two-phase-commit-lab/`
- static HTML comparison dashboards for recruiter screenshots, GitHub Pages browsing, or interview walkthrough links
- multi-scenario catalog generation that regenerates per-scenario reports and writes a portfolio-friendly landing page comparing outcomes, reconnect recoveries, termination hints, and any committed comparison/termination companion artifacts in one place
- clean CLI commands for validation, single-scenario simulation, protocol comparison, and bundle generation

## Project structure
- `two_phase_commit_lab.py` - validator, simulator, peer-resolution/2PC-vs-saga artifact generators (Markdown/JSON/HTML), catalog generator, and CLI entrypoint
- `order_success.json` - all participants vote YES and the transaction commits
- `payment_validation_abort.json` - one participant votes NO so the transaction aborts globally
- `coordinator_crash_before_decision.json` - all participants prepare, but the coordinator crashes before a durable outcome exists
- `coordinator_crash_partial_commit_delivery.json` - the coordinator logs COMMIT, one participant hears it, then the coordinator crashes while other prepared peers remain blocked
- `coordinator_crash_durable_abort.json` - the coordinator logs ABORT, crashes before the prepared YES-voters hear it, and leaves a blocked case that peers can still resolve safely
- `coordinator_recovery_commit.json` - the coordinator logs COMMIT, crashes, then replays the decision during recovery
- `participant_reconnect_commit.json` - a prepared participant misses the first `COMMIT`, reconnects, and resolves the durable outcome safely
- `CHECKLIST.md` - resumable slice history plus next ideas
- `tests/test_two_phase_commit_lab.py` - regression tests for validation, simulation, comparison mode, HTML/Markdown CLI output, and catalog generation
- `docs/artifacts/two-phase-commit-lab/` - committed per-scenario reports, peer-resolution artifacts, the scenario catalog landing page, and protocol-comparison Markdown/JSON/HTML artifacts with cross-links between them when the companion files exist

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

### Compare 2PC with an orchestrated saga for the same incident
```bash
python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare \
  projects/two-phase-commit-lab/coordinator_crash_before_decision.json \
  --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.md \
  --html-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.html \
  --json
```

### Simulate the peer-to-peer termination protocol after a blocked run
```bash
python3 projects/two-phase-commit-lab/two_phase_commit_lab.py terminate \
  projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json \
  --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_termination.md \
  --json
```

```bash
python3 projects/two-phase-commit-lab/two_phase_commit_lab.py terminate \
  projects/two-phase-commit-lab/coordinator_crash_durable_abort.json \
  --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_durable_abort_termination.md \
  --json
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
- `coordinator_crash_durable_abort.json`
  - blocked-after-ABORT incidents also have an actionable peer story: a participant that never reached PREPARED can prove that rollback is the only safe outcome
- `coordinator_recovery_commit.json`
  - once the decision log is durable, recovery can safely replay COMMIT and finish the protocol after a crash
- `participant_reconnect_commit.json`
  - a prepared participant can still end up temporarily in doubt after missing the first second-phase message, then safely finish by reconnecting to learn the durable decision
- `scenario_catalog.md`
  - one landing page compares all committed scenarios and now deep-links into per-scenario reports, protocol-comparison dashboards/Markdown, and peer-termination walkthroughs whenever those companion artifacts exist
- `coordinator_crash_before_decision_protocol_compare.md` / `.html`
  - a side-by-side 2PC vs saga artifact for the classic blocking crash, useful when interviewers ask why microservices often avoid plain 2PC
- `coordinator_crash_partial_commit_delivery_protocol_compare.md` / `.html`
  - a peer-visible-decision comparison artifact showing that some blocked 2PC incidents still have an actionable termination-protocol story before coordinator recovery
- `coordinator_crash_partial_commit_delivery_termination.md`
  - the blocked-after-decision case fully resolves via peer queries because `inventory` already knows the durable `COMMIT`
- `coordinator_crash_before_decision_termination.md`
  - the classic all-prepared crash still cannot resolve through peers alone, which keeps the blocking limitation obvious in artifact form
- `coordinator_crash_durable_abort_termination.md`
  - the blocked-after-ABORT case resolves safely because `risk` never reached `PREPARED`, so it can prove rollback to the waiting peers

## Testing
```bash
python3 -m unittest tests.test_two_phase_commit_lab -v
```

## Future ideas
- add a side-by-side 2PC vs 3PC comparison mode to explain why non-blocking atomic commit is harder
- add scenario tags or thematic groupings (happy path, blocking, coordinator recovery, participant reconnect, peer hints, peer-assisted commit, peer-assisted abort) inside the catalog if the sample set grows larger
- consider a small incident-response timeline or sequence diagram export for the termination-resolution flow

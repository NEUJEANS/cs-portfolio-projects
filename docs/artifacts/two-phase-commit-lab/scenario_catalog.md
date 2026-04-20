# Two-phase commit scenario catalog

A recruiter-friendly landing page for the committed 2PC scenarios, showing how the same protocol behaves across happy-path, veto, blocking, recovery, and peer-assisted incident-response cases.

## Bundle summary
- scenarios: `7`
- outcomes: `3 commit`, `1 abort`, `3 blocked`
- crash cases: `4`
- coordinator recovery cases: `1`
- participant reconnect recoveries: `1`
- blocked scenarios with actionable peer hints: `2`
- scenarios with protocol-comparison dashboards: `2`
- scenarios with peer-termination walkthroughs: `3`

## Scenario comparison
| Scenario | Outcome | Decision | Durable decision | Crash point | Recovery | Prepared | Acked | Recovered after reconnect | Termination hint | Report | Compare | Termination |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Coordinator crash before durable decision](coordinator_crash_before_decision_report.md) | `blocked` | `none` | `no` | `before-decision` | `no` | `3/3` | `0/3` | `-` | wait: all prepared peers are still uncertain | [report](coordinator_crash_before_decision_report.md) | [html](coordinator_crash_before_decision_protocol_compare.html) / [md](coordinator_crash_before_decision_protocol_compare.md) | [md](coordinator_crash_before_decision_termination.md) |
| [Coordinator crash after durable ABORT](coordinator_crash_durable_abort_report.md) | `blocked` | `abort` | `yes` | `after-decision-log` | `no` | `2/3` | `0/3` | `-` | ABORT safe via risk | [report](coordinator_crash_durable_abort_report.md) | - | [md](coordinator_crash_durable_abort_termination.md) |
| [Coordinator crash after one COMMIT delivery](coordinator_crash_partial_commit_delivery_report.md) | `blocked` | `commit` | `yes` | `after-decision-log` | `no` | `3/3` | `1/3` | `-` | COMMIT visible via inventory | [report](coordinator_crash_partial_commit_delivery_report.md) | [html](coordinator_crash_partial_commit_delivery_protocol_compare.html) / [md](coordinator_crash_partial_commit_delivery_protocol_compare.md) | [md](coordinator_crash_partial_commit_delivery_termination.md) |
| [Recovery replays a durable commit](coordinator_recovery_commit_report.md) | `commit` | `commit` | `yes` | `after-decision-log` | `yes` | `3/3` | `3/3` | `-` | - | [report](coordinator_recovery_commit_report.md) | - | - |
| [Order service happy-path commit](order_success_report.md) | `commit` | `commit` | `yes` | `none` | `no` | `3/3` | `3/3` | `-` | - | [report](order_success_report.md) | - | - |
| [Participant reconnect resolves a missed COMMIT](participant_reconnect_commit_report.md) | `commit` | `commit` | `yes` | `none` | `no` | `3/3` | `3/3` | `1/1` | - | [report](participant_reconnect_commit_report.md) | - | - |
| [Fraud check forces global abort](payment_validation_abort_report.md) | `abort` | `abort` | `yes` | `none` | `no` | `2/3` | `2/3` | `-` | - | [report](payment_validation_abort_report.md) | - | - |

## Interview talking points
- plain 2PC is easy to explain because every scenario pivots on the coordinator's durable decision log.
- blocking shows up when participants are already prepared but cannot prove the final outcome after a coordinator crash.
- participant-side reconnects matter too: even with a durable decision, a prepared participant can stay in doubt until the coordinator retries or recovery answers the query.
- when the coordinator is down, participants can still ask peers whether anyone already knows the durable decision or never reached PREPARED; otherwise the protocol remains blocked.
- recovery is operationally different from blocking: once the decision is durable, replay can safely finish phase two.

## Scenario snapshots
### Coordinator crash before durable decision
- source: `projects/two-phase-commit-lab/coordinator_crash_before_decision.json`
- description: Every participant votes YES and enters PREPARED, but the coordinator crashes before it records COMMIT or ABORT. This is the classic blocking case that makes plain 2PC operationally painful.
- outcome: `blocked` with decision `none`
- participants prepared/acked: `3/3` prepared, `0/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: wait: all prepared peers are still uncertain
- why it matters: all participants are prepared, but the coordinator crashed before a durable decision was recorded; prepared participants remain blocked awaiting recovery
- related artifacts: [report](coordinator_crash_before_decision_report.md) / [compare html](coordinator_crash_before_decision_protocol_compare.html) / [compare md](coordinator_crash_before_decision_protocol_compare.md) / [termination md](coordinator_crash_before_decision_termination.md)

### Coordinator crash after durable ABORT
- source: `projects/two-phase-commit-lab/coordinator_crash_durable_abort.json`
- description: Inventory and billing vote YES, but risk votes NO. The coordinator durably logs ABORT and crashes before the prepared YES-voters hear the decision. They are blocked in classic 2PC, but a peer-to-peer termination check can still prove ABORT safely because risk never reached PREPARED.
- outcome: `blocked` with decision `abort`
- participants prepared/acked: `2/3` prepared, `0/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: ABORT safe via risk
- why it matters: blocked does not always mean blind waiting: ABORT safe via risk.
- related artifacts: [report](coordinator_crash_durable_abort_report.md) / [termination md](coordinator_crash_durable_abort_termination.md)

### Coordinator crash after one COMMIT delivery
- source: `projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json`
- description: All participants vote YES and the coordinator durably logs COMMIT. Inventory hears the second-phase COMMIT first, then the coordinator crashes before billing and shipping hear it. The remaining prepared participants are blocked, but a peer-to-peer termination check can still learn COMMIT from inventory while waiting for recovery.
- outcome: `blocked` with decision `commit`
- participants prepared/acked: `3/3` prepared, `1/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: COMMIT visible via inventory
- why it matters: blocked does not always mean blind waiting: COMMIT visible via inventory.
- related artifacts: [report](coordinator_crash_partial_commit_delivery_report.md) / [compare html](coordinator_crash_partial_commit_delivery_protocol_compare.html) / [compare md](coordinator_crash_partial_commit_delivery_protocol_compare.md) / [termination md](coordinator_crash_partial_commit_delivery_termination.md)

### Recovery replays a durable commit
- source: `projects/two-phase-commit-lab/coordinator_recovery_commit.json`
- description: All participants vote YES, the coordinator durably logs COMMIT, then crashes before everyone hears the outcome. Recovery replays the log and safely finishes phase two.
- outcome: `commit` with decision `commit`
- participants prepared/acked: `3/3` prepared, `3/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: -
- why it matters: 2PC commits only because every participant voted YES and the coordinator recorded a durable COMMIT decision.
- related artifacts: [report](coordinator_recovery_commit_report.md)

### Order service happy-path commit
- source: `projects/two-phase-commit-lab/order_success.json`
- description: Inventory, billing, and shipping all vote YES, so the coordinator records a durable commit and every participant applies the order in the second phase.
- outcome: `commit` with decision `commit`
- participants prepared/acked: `3/3` prepared, `3/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: -
- why it matters: 2PC commits only because every participant voted YES and the coordinator recorded a durable COMMIT decision.
- related artifacts: [report](order_success_report.md)

### Participant reconnect resolves a missed COMMIT
- source: `projects/two-phase-commit-lab/participant_reconnect_commit.json`
- description: All participants vote YES and the coordinator durably logs COMMIT, but shipping misses the first second-phase message during a disconnect. After timing out in PREPARED, it reconnects, learns the durable decision, and safely commits.
- outcome: `commit` with decision `commit`
- participants prepared/acked: `3/3` prepared, `3/3` acked
- participant reconnect recovery: `1/1` recovered after missing the first second-phase delivery
- termination hint: -
- why it matters: 1 participant missed the first second-phase delivery, and 1 participant later recovered by reconnecting for the durable decision.
- related artifacts: [report](participant_reconnect_commit_report.md)

### Fraud check forces global abort
- source: `projects/two-phase-commit-lab/payment_validation_abort.json`
- description: Inventory is ready, but the risk service votes NO after a fraud signal. The coordinator must abort the whole distributed transaction so no participant commits alone.
- outcome: `abort` with decision `abort`
- participants prepared/acked: `2/3` prepared, `2/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: -
- why it matters: 2PC aborts whenever a participant refuses, times out, or recovery cannot prove a durable COMMIT record.
- related artifacts: [report](payment_validation_abort_report.md)

# Two-phase commit scenario catalog

A recruiter-friendly landing page for the committed 2PC scenarios, showing how the same protocol behaves across happy-path, veto, blocking, and recovery cases.

## Bundle summary
- scenarios: `4`
- outcomes: `2 commit`, `1 abort`, `1 blocked`
- crash cases: `2`
- recovery cases: `1`

## Scenario comparison
| Scenario | Outcome | Decision | Durable decision | Crash point | Recovery | Prepared | Acked | Report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Coordinator crash before durable decision](coordinator_crash_before_decision_report.md) | `blocked` | `none` | `no` | `before-decision` | `no` | `3/3` | `0/3` | [report](coordinator_crash_before_decision_report.md) |
| [Recovery replays a durable commit](coordinator_recovery_commit_report.md) | `commit` | `commit` | `yes` | `after-decision-log` | `yes` | `3/3` | `3/3` | [report](coordinator_recovery_commit_report.md) |
| [Order service happy-path commit](order_success_report.md) | `commit` | `commit` | `yes` | `none` | `no` | `3/3` | `3/3` | [report](order_success_report.md) |
| [Fraud check forces global abort](payment_validation_abort_report.md) | `abort` | `abort` | `yes` | `none` | `no` | `2/3` | `2/3` | [report](payment_validation_abort_report.md) |

## Interview talking points
- plain 2PC is easy to explain because every scenario pivots on the coordinator's durable decision log.
- blocking shows up when participants are already prepared but cannot prove the final outcome after a coordinator crash.
- recovery is operationally different from blocking: once the decision is durable, replay can safely finish phase two.

## Scenario snapshots
### Coordinator crash before durable decision
- source: `projects/two-phase-commit-lab/coordinator_crash_before_decision.json`
- description: Every participant votes YES and enters PREPARED, but the coordinator crashes before it records COMMIT or ABORT. This is the classic blocking case that makes plain 2PC operationally painful.
- outcome: `blocked` with decision `none`
- participants prepared/acked: `3/3` prepared, `0/3` acked
- why it matters: all participants are prepared, but the coordinator crashed before a durable decision was recorded; prepared participants remain blocked awaiting recovery
- deep dive: [coordinator_crash_before_decision_report.md](coordinator_crash_before_decision_report.md)

### Recovery replays a durable commit
- source: `projects/two-phase-commit-lab/coordinator_recovery_commit.json`
- description: All participants vote YES, the coordinator durably logs COMMIT, then crashes before everyone hears the outcome. Recovery replays the log and safely finishes phase two.
- outcome: `commit` with decision `commit`
- participants prepared/acked: `3/3` prepared, `3/3` acked
- why it matters: 2PC commits only because every participant voted YES and the coordinator recorded a durable COMMIT decision.
- deep dive: [coordinator_recovery_commit_report.md](coordinator_recovery_commit_report.md)

### Order service happy-path commit
- source: `projects/two-phase-commit-lab/order_success.json`
- description: Inventory, billing, and shipping all vote YES, so the coordinator records a durable commit and every participant applies the order in the second phase.
- outcome: `commit` with decision `commit`
- participants prepared/acked: `3/3` prepared, `3/3` acked
- why it matters: 2PC commits only because every participant voted YES and the coordinator recorded a durable COMMIT decision.
- deep dive: [order_success_report.md](order_success_report.md)

### Fraud check forces global abort
- source: `projects/two-phase-commit-lab/payment_validation_abort.json`
- description: Inventory is ready, but the risk service votes NO after a fraud signal. The coordinator must abort the whole distributed transaction so no participant commits alone.
- outcome: `abort` with decision `abort`
- participants prepared/acked: `2/3` prepared, `2/3` acked
- why it matters: 2PC aborts whenever a participant refuses, times out, or recovery cannot prove a durable COMMIT record.
- deep dive: [payment_validation_abort_report.md](payment_validation_abort_report.md)

# Two-phase commit scenario catalog

A recruiter-friendly landing page for the committed 2PC scenarios, showing how the same protocol behaves across happy-path, veto, blocking, recovery, and peer-assisted incident-response cases.

## Active filters
- bundle preset: `baseline-flows` (happy-path and veto scenarios that establish the normal 2PC commit/abort baseline before crash drills.)
- scenario tags: `any` of `baseline`
- this bundle is a recruiter-friendly subset of the provided scenario set rather than the full catalog

## Bundle summary
- scenarios: `2`
- outcomes: `1 commit`, `1 abort`, `0 blocked`
- crash cases: `0`
- coordinator recovery cases: `0`
- participant reconnect recoveries: `0`
- scenario tags: `5` unique
- blocked scenarios with actionable peer hints: `0`
- scenarios with protocol-comparison dashboards: `0`
- scenarios with peer-termination walkthroughs: `0`
- scenarios with peer-termination timeline visuals: `0`

## Theme groups
Browse the bundle by scenario theme when you want only blocking incidents, recovery drills, or participant-side reconnect stories.

### `baseline`
- scenarios: `2`
- includes: [Order service happy-path commit](order_success_report.md); [Fraud check forces global abort](payment_validation_abort_report.md)

### `commit`
- scenarios: `1`
- includes: [Order service happy-path commit](order_success_report.md)

## Scenario comparison
| Scenario | Tags | Outcome | Decision | Durable decision | Crash point | Recovery | Prepared | Acked | Recovered after reconnect | Termination hint | Report | Compare | Termination | Timeline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Order service happy-path commit](order_success_report.md) | `happy-path`, `commit`, `baseline` | `commit` | `commit` | `yes` | `none` | `no` | `3/3` | `3/3` | `-` | - | [report](order_success_report.md) | - | - | - |
| [Fraud check forces global abort](payment_validation_abort_report.md) | `abort`, `veto`, `baseline` | `abort` | `abort` | `yes` | `none` | `no` | `2/3` | `2/3` | `-` | - | [report](payment_validation_abort_report.md) | - | - | - |

## Interview talking points
- plain 2PC is easy to explain because every scenario pivots on the coordinator's durable decision log.
- blocking shows up when participants are already prepared but cannot prove the final outcome after a coordinator crash.
- participant-side reconnects matter too: even with a durable decision, a prepared participant can stay in doubt until the coordinator retries or recovery answers the query.
- when the coordinator is down, participants can still ask peers whether anyone already knows the durable decision or never reached PREPARED; otherwise the protocol remains blocked.
- recovery is operationally different from blocking: once the decision is durable, replay can safely finish phase two.

## Scenario snapshots
### Order service happy-path commit
- source: `projects/two-phase-commit-lab/order_success.json`
- description: Inventory, billing, and shipping all vote YES, so the coordinator records a durable commit and every participant applies the order in the second phase.
- tags: `happy-path`, `commit`, `baseline`
- outcome: `commit` with decision `commit`
- participants prepared/acked: `3/3` prepared, `3/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: -
- why it matters: 2PC commits only because every participant voted YES and the coordinator recorded a durable COMMIT decision.
- related artifacts: [report](order_success_report.md)

### Fraud check forces global abort
- source: `projects/two-phase-commit-lab/payment_validation_abort.json`
- description: Inventory is ready, but the risk service votes NO after a fraud signal. The coordinator must abort the whole distributed transaction so no participant commits alone.
- tags: `abort`, `veto`, `baseline`
- outcome: `abort` with decision `abort`
- participants prepared/acked: `2/3` prepared, `2/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: -
- why it matters: 2PC aborts whenever a participant refuses, times out, or recovery cannot prove a durable COMMIT record.
- related artifacts: [report](payment_validation_abort_report.md)

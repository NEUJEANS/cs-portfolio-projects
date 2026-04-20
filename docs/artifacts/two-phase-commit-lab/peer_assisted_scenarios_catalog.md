# Two-phase commit scenario catalog

A recruiter-friendly landing page for the committed 2PC scenarios, showing how the same protocol behaves across happy-path, veto, blocking, recovery, and peer-assisted incident-response cases.

Need the blocked-case triage view first? Open the [incident-response dashboard](peer_assisted_scenarios_catalog_incident_response_dashboard.html).

## Active filters
- scenario tags: `any` of `peer-assisted-commit`, `peer-assisted-abort`
- this bundle is a recruiter-friendly subset of the provided scenario set rather than the full catalog

## Bundle summary
- scenarios: `2`
- outcomes: `0 commit`, `0 abort`, `2 blocked`
- crash cases: `2`
- coordinator recovery cases: `0`
- participant reconnect recoveries: `0`
- scenario tags: `4` unique
- blocked scenarios with actionable peer hints: `2`
- scenarios with protocol-comparison dashboards: `1`
- scenarios with peer-termination walkthroughs: `2`
- scenarios with peer-termination timeline visuals: `2`

## Theme groups
Browse the bundle by scenario theme when you want only blocking incidents, recovery drills, or participant-side reconnect stories.

### `blocking`
- scenarios: `2`
- includes: [Coordinator crash after durable ABORT](coordinator_crash_durable_abort_report.md); [Coordinator crash after one COMMIT delivery](coordinator_crash_partial_commit_delivery_report.md)

### `crash`
- scenarios: `2`
- includes: [Coordinator crash after durable ABORT](coordinator_crash_durable_abort_report.md); [Coordinator crash after one COMMIT delivery](coordinator_crash_partial_commit_delivery_report.md)

### `peer-assisted-abort`
- scenarios: `1`
- includes: [Coordinator crash after durable ABORT](coordinator_crash_durable_abort_report.md)

### `peer-assisted-commit`
- scenarios: `1`
- includes: [Coordinator crash after one COMMIT delivery](coordinator_crash_partial_commit_delivery_report.md)

## Scenario comparison
| Scenario | Tags | Outcome | Decision | Durable decision | Crash point | Recovery | Prepared | Acked | Recovered after reconnect | Termination hint | Report | Compare | Termination | Timeline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Coordinator crash after durable ABORT](coordinator_crash_durable_abort_report.md) | `blocking`, `crash`, `peer-assisted-abort` | `blocked` | `abort` | `yes` | `after-decision-log` | `no` | `2/3` | `0/3` | `-` | ABORT safe via risk | [report](coordinator_crash_durable_abort_report.md) | - | [md](coordinator_crash_durable_abort_termination.md) | [html](coordinator_crash_durable_abort_termination_timeline.html) / [svg](coordinator_crash_durable_abort_termination_timeline.svg) |
| [Coordinator crash after one COMMIT delivery](coordinator_crash_partial_commit_delivery_report.md) | `blocking`, `crash`, `peer-assisted-commit` | `blocked` | `commit` | `yes` | `after-decision-log` | `no` | `3/3` | `1/3` | `-` | COMMIT visible via inventory | [report](coordinator_crash_partial_commit_delivery_report.md) | [html](coordinator_crash_partial_commit_delivery_protocol_compare.html) / [md](coordinator_crash_partial_commit_delivery_protocol_compare.md) | [md](coordinator_crash_partial_commit_delivery_termination.md) | [html](coordinator_crash_partial_commit_delivery_termination_timeline.html) / [svg](coordinator_crash_partial_commit_delivery_termination_timeline.svg) |

## Interview talking points
- plain 2PC is easy to explain because every scenario pivots on the coordinator's durable decision log.
- blocking shows up when participants are already prepared but cannot prove the final outcome after a coordinator crash.
- participant-side reconnects matter too: even with a durable decision, a prepared participant can stay in doubt until the coordinator retries or recovery answers the query.
- when the coordinator is down, participants can still ask peers whether anyone already knows the durable decision or never reached PREPARED; otherwise the protocol remains blocked.
- recovery is operationally different from blocking: once the decision is durable, replay can safely finish phase two.

## Scenario snapshots
### Coordinator crash after durable ABORT
- source: `projects/two-phase-commit-lab/coordinator_crash_durable_abort.json`
- description: Inventory and billing vote YES, but risk votes NO. The coordinator durably logs ABORT and crashes before the prepared YES-voters hear the decision. They are blocked in classic 2PC, but a peer-to-peer termination check can still prove ABORT safely because risk never reached PREPARED.
- tags: `blocking`, `crash`, `peer-assisted-abort`
- outcome: `blocked` with decision `abort`
- participants prepared/acked: `2/3` prepared, `0/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: ABORT safe via risk
- why it matters: blocked does not always mean blind waiting: ABORT safe via risk.
- related artifacts: [report](coordinator_crash_durable_abort_report.md) / [termination md](coordinator_crash_durable_abort_termination.md) / [timeline html](coordinator_crash_durable_abort_termination_timeline.html) / [timeline svg](coordinator_crash_durable_abort_termination_timeline.svg)

### Coordinator crash after one COMMIT delivery
- source: `projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json`
- description: All participants vote YES and the coordinator durably logs COMMIT. Inventory hears the second-phase COMMIT first, then the coordinator crashes before billing and shipping hear it. The remaining prepared participants are blocked, but a peer-to-peer termination check can still learn COMMIT from inventory while waiting for recovery.
- tags: `blocking`, `crash`, `peer-assisted-commit`
- outcome: `blocked` with decision `commit`
- participants prepared/acked: `3/3` prepared, `1/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: COMMIT visible via inventory
- why it matters: blocked does not always mean blind waiting: COMMIT visible via inventory.
- related artifacts: [report](coordinator_crash_partial_commit_delivery_report.md) / [compare html](coordinator_crash_partial_commit_delivery_protocol_compare.html) / [compare md](coordinator_crash_partial_commit_delivery_protocol_compare.md) / [termination md](coordinator_crash_partial_commit_delivery_termination.md) / [timeline html](coordinator_crash_partial_commit_delivery_termination_timeline.html) / [timeline svg](coordinator_crash_partial_commit_delivery_termination_timeline.svg)

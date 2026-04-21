# Two-phase commit scenario catalog

A recruiter-friendly landing page for the committed 2PC scenarios, showing how the same protocol behaves across happy-path, veto, blocking, recovery, and peer-assisted incident-response cases.

## Active filters
- bundle preset: `recovery-story` (durable-decision replay plus participant reconnect stories that show how doubt clears after a failure.)
- scenario tags: `any` of `recovery`, `participant-reconnect`
- this bundle is a recruiter-friendly subset of the provided scenario set rather than the full catalog

## Bundle summary
- scenarios: `2`
- outcomes: `2 commit`, `0 abort`, `0 blocked`
- crash cases: `1`
- coordinator recovery cases: `1`
- participant reconnect recoveries: `1`
- scenario tags: `6` unique
- blocked scenarios with actionable peer hints: `0`
- scenarios with protocol-comparison dashboards: `0`
- scenarios with peer-termination walkthroughs: `0`
- scenarios with peer-termination timeline visuals: `0`
- scenarios with blocked timeline PNG covers: `0`

## Theme groups
Browse the bundle by scenario theme when you want only blocking incidents, recovery drills, or participant-side reconnect stories.

### `commit`
- scenarios: `1`
- includes: [Participant reconnect resolves a missed COMMIT](participant_reconnect_commit_report.md)

### `crash`
- scenarios: `1`
- includes: [Recovery replays a durable commit](coordinator_recovery_commit_report.md)

### `participant-reconnect`
- scenarios: `1`
- includes: [Participant reconnect resolves a missed COMMIT](participant_reconnect_commit_report.md)

### `recovery`
- scenarios: `1`
- includes: [Recovery replays a durable commit](coordinator_recovery_commit_report.md)

## Scenario comparison
| Scenario | Tags | Outcome | Decision | Durable decision | Crash point | Recovery | Prepared | Acked | Recovered after reconnect | Termination hint | Report | Compare | Termination | Timeline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Recovery replays a durable commit](coordinator_recovery_commit_report.md) | `recovery`, `crash`, `commit-replay` | `commit` | `commit` | `yes` | `after-decision-log` | `yes` | `3/3` | `3/3` | `-` | - | [report](coordinator_recovery_commit_report.md) | - | - | - |
| [Participant reconnect resolves a missed COMMIT](participant_reconnect_commit_report.md) | `participant-reconnect`, `missed-delivery`, `commit` | `commit` | `commit` | `yes` | `none` | `no` | `3/3` | `3/3` | `1/1` | - | [report](participant_reconnect_commit_report.md) | - | - | - |

## Interview talking points
- plain 2PC is easy to explain because every scenario pivots on the coordinator's durable decision log.
- blocking shows up when participants are already prepared but cannot prove the final outcome after a coordinator crash.
- participant-side reconnects matter too: even with a durable decision, a prepared participant can stay in doubt until the coordinator retries or recovery answers the query.
- when the coordinator is down, participants can still ask peers whether anyone already knows the durable decision or never reached PREPARED; otherwise the protocol remains blocked.
- recovery is operationally different from blocking: once the decision is durable, replay can safely finish phase two.

## Scenario snapshots
### Recovery replays a durable commit
- source: `projects/two-phase-commit-lab/coordinator_recovery_commit.json`
- description: All participants vote YES, the coordinator durably logs COMMIT, then crashes before everyone hears the outcome. Recovery replays the log and safely finishes phase two.
- tags: `recovery`, `crash`, `commit-replay`
- outcome: `commit` with decision `commit`
- participants prepared/acked: `3/3` prepared, `3/3` acked
- participant reconnect recovery: `-` (no participant missed the first second-phase delivery)
- termination hint: -
- why it matters: 2PC commits only because every participant voted YES and the coordinator recorded a durable COMMIT decision.
- related artifacts: [report](coordinator_recovery_commit_report.md)

### Participant reconnect resolves a missed COMMIT
- source: `projects/two-phase-commit-lab/participant_reconnect_commit.json`
- description: All participants vote YES and the coordinator durably logs COMMIT, but shipping misses the first second-phase message during a disconnect. After timing out in PREPARED, it reconnects, learns the durable decision, and safely commits.
- tags: `participant-reconnect`, `missed-delivery`, `commit`
- outcome: `commit` with decision `commit`
- participants prepared/acked: `3/3` prepared, `3/3` acked
- participant reconnect recovery: `1/1` recovered after missing the first second-phase delivery
- termination hint: -
- why it matters: 1 participant missed the first second-phase delivery, and 1 participant later recovered by reconnecting for the durable decision.
- related artifacts: [report](participant_reconnect_commit_report.md)

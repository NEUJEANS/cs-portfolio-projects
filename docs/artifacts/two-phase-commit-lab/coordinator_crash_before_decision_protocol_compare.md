# Coordinator crash before durable decision protocol comparison

Every participant votes YES and enters PREPARED, but the coordinator crashes before it records COMMIT or ABORT. This is the classic blocking case that makes plain 2PC operationally painful.

## Scenario snapshot
- transaction id: `order-2021`
- participants: `3` total (`3` commit, `0` abort, `0` timeout)
- coordinator crash point: `before-decision`
- coordinator recovery simulated: `no`
- participant-configured missed second-phase deliveries: `0` (none)
- participants that learned the final 2PC decision: `0` (none yet)
- 2PC baseline outcome: `blocked`
- termination hint in the 2PC baseline: wait: all prepared peers are still uncertain

## Protocol contrast
| Protocol | Outcome in this scenario | Consistency model | Atomicity | Blocking behavior | Recovery story |
| --- | --- | --- | --- | --- | --- |
| 2PC | `blocked` | strong atomic commit when the decision completes; every participant follows the same global outcome | global all-or-nothing across participants once the coordinator's durable decision is known | blocking once PREPARED participants cannot prove the coordinator's final decision | needs coordinator recovery or a safe termination-protocol answer from an authoritative peer |
| Saga (orchestrated) | `paused-not-blocked` | eventual consistency across services, with explicit compensations when later steps fail | no single global atomic commit; earlier local success is repaired by compensation instead of a shared PREPARE/COMMIT barrier | non-blocking for participant resources; the workflow can pause, but services do not sit on PREPARED locks waiting for a global decision | resume from the last durable saga step or compensate the already-finished steps; no global prepare barrier needs to be unblocked |

## Protocol notes
### 2PC
- coordination model: single coordinator with PREPARE and COMMIT/ABORT phases over durable decision logging
- participant story: 3/3 participants reached PREPARED and 0/3 learned the final decision in this run
- interview hook: 2PC buys atomic all-or-nothing semantics, but the price is visible coordinator-centered blocking in outage scenarios.
- tradeoffs:
  - easy to explain when interviewers ask how a durable decision log enforces atomic commit
  - participants may hold PREPARED state while waiting on the coordinator or an authoritative replay
  - fits tightly coupled all-or-nothing workflows better than high-availability microservice traffic

### Saga (orchestrated)
- coordination model: ordered local transactions plus compensating actions, typically driven by an orchestrator or event flow
- participant story: already-finished local transactions stay committed, unfinished steps pause for orchestrator recovery or operator action, and peers continue serving other work
- interview hook: A saga can still stall operationally, but it stalls as resumable workflow state instead of coordinator-driven prepared-lock blocking.
- tradeoffs:
  - fits database-per-service architectures because each step owns only its local database transaction
  - developers must design idempotent retries and compensating actions instead of relying on automatic rollback
  - availability is usually better than plain 2PC, but isolation is weaker and temporary anomalies are possible

## Interview takeaways
- In this scenario, plain 2PC resolves as `blocked`, which is driven by one coordinator-owned durable decision and the PREPARED states around it.
- An orchestrated saga would avoid PREPARED lock blocking by committing local work independently and using retries/compensations instead of a global commit barrier.
- Use this comparison to explain why high-availability microservice systems often choose sagas when temporary inconsistency is acceptable but indefinite coordinator blocking is not.
- The configured crash point (`before-decision`) is the teaching lever here: it shows that the same business transaction can become either coordinator-blocked (2PC) or resumable/compensatable (saga).

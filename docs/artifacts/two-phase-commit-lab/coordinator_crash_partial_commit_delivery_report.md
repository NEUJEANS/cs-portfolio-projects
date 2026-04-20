# Coordinator crash after one COMMIT delivery

All participants vote YES and the coordinator durably logs COMMIT. Inventory hears the second-phase COMMIT first, then the coordinator crashes before billing and shipping hear it. The remaining prepared participants are blocked, but a peer-to-peer termination check can still learn COMMIT from inventory while waiting for recovery.

## Outcome
- transaction id: `order-5120`
- scenario tags: `blocking`, `crash`, `peer-assisted-commit`
- final outcome: `blocked`
- durable decision recorded: `yes`
- coordinator crash point: `after-decision-log`
- coordinator recovery simulated: `no`
- configured decision deliveries before crash: `1`
- successful decision deliveries before crash: `1`
- blocking reason: the durable COMMIT decision exists and inventory already knows it, but billing and shipping remain in doubt until coordinator recovery or a peer-to-peer termination check
- termination hint summary: COMMIT visible via inventory

## Participant summary
| Participant | Role | Planned vote | 2nd-phase delivery | Final state | Acked decision | Recovered after reconnect | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| inventory | reserve stock | commit | deliver | committed | yes | no | inventory hears COMMIT before the coordinator dies |
| billing | capture payment | commit | deliver | prepared | no | no | payment is still prepared and waiting for a final answer |
| shipping | create shipment | commit | deliver | prepared | no | no | shipment remains in doubt until it learns the durable outcome |

## Termination protocol hints
- Ask reachable peers whether anyone already knows the final decision. Here, inventory already knows `COMMIT` and can relay it to billing and shipping.
- Treat the peer answer as evidence of the coordinator's durable outcome, not permission to invent a brand-new one locally.
- If no informed peer is reachable, the unresolved participants still need coordinator recovery or another authoritative replay.

## Trace
1. coordinator starts 2PC for order-5120 with 3 participants
2. coordinator -> inventory: PREPARE
3. inventory: writes PREPARED record and replies YES
4. coordinator -> billing: PREPARE
5. billing: writes PREPARED record and replies YES
6. coordinator -> shipping: PREPARE
7. shipping: writes PREPARED record and replies YES
8. coordinator writes COMMIT decision to durable log
9. coordinator -> inventory: COMMIT
10. inventory: commits local work and acknowledges COMMIT
11. coordinator reaches 1 participant(s) with the durable COMMIT decision before crashing
12. coordinator crashes after the durable decision is logged but before all participants hear it
13. some prepared participants still lack the final decision and remain blocked until coordinator recovery or a termination-protocol exchange

## Takeaways
- 3 participants were willing to commit, 0 voted abort, and 0 timed out.
- 3 participants reached PREPARED before the transaction finished.
- 1 participant already knows the durable COMMIT while other prepared peers remain blocked.
- the durable COMMIT decision exists and inventory already knows it, but billing and shipping remain in doubt until coordinator recovery or a peer-to-peer termination check
- Final coordinator state: crashed-after-decision.

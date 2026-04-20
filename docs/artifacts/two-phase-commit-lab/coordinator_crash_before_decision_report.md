# Coordinator crash before durable decision

Every participant votes YES and enters PREPARED, but the coordinator crashes before it records COMMIT or ABORT. This is the classic blocking case that makes plain 2PC operationally painful.

## Outcome
- transaction id: `order-2021`
- final outcome: `blocked`
- durable decision recorded: `no`
- coordinator crash point: `before-decision`
- coordinator recovery simulated: `no`
- configured decision deliveries before crash: `0`
- successful decision deliveries before crash: `0`
- blocking reason: all participants are prepared, but the coordinator crashed before a durable decision was recorded; prepared participants remain blocked awaiting recovery
- termination hint summary: wait: all prepared peers are still uncertain

## Participant summary
| Participant | Role | Planned vote | 2nd-phase delivery | Final state | Acked decision | Recovered after reconnect | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| inventory | reserve stock | commit | deliver | prepared | no | no | local reservation is durable but not final |
| billing | capture payment | commit | deliver | prepared | no | no | payment provider is waiting for final confirmation |
| shipping | create shipment | commit | deliver | prepared | no | no | label request is staged but not finalized |

## Termination protocol hints
- Ask reachable peers whether anyone already knows COMMIT/ABORT or never reached PREPARED.
- In this run, inventory, billing, and shipping are still PREPARED/in doubt, so the classic termination protocol cannot finish safely yet.
- Keep waiting for coordinator recovery; plain 2PC stays blocked when every reachable participant is uncertain.

## Trace
1. coordinator starts 2PC for order-2021 with 3 participants
2. coordinator -> inventory: PREPARE
3. inventory: writes PREPARED record and replies YES
4. coordinator -> billing: PREPARE
5. billing: writes PREPARED record and replies YES
6. coordinator -> shipping: PREPARE
7. shipping: writes PREPARED record and replies YES
8. coordinator crashes after collecting YES votes but before writing a durable decision
9. participants remain blocked in PREPARED because no coordinator decision is available

## Takeaways
- 3 participants were willing to commit, 0 voted abort, and 0 timed out.
- 3 participants reached PREPARED before the transaction finished.
- all participants are prepared, but the coordinator crashed before a durable decision was recorded; prepared participants remain blocked awaiting recovery
- Final coordinator state: crashed-before-decision.

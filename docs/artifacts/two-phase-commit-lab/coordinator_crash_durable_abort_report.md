# Coordinator crash after durable ABORT

Inventory and billing vote YES, but risk votes NO. The coordinator durably logs ABORT and crashes before the prepared YES-voters hear the decision. They are blocked in classic 2PC, but a peer-to-peer termination check can still prove ABORT safely because risk never reached PREPARED.

## Outcome
- transaction id: `order-6112`
- final outcome: `blocked`
- durable decision recorded: `yes`
- coordinator crash point: `after-decision-log`
- coordinator recovery simulated: `no`
- configured decision deliveries before crash: `0`
- successful decision deliveries before crash: `0`
- blocking reason: the durable ABORT decision exists, but no prepared participant has learned it yet; prepared participants stay in doubt until recovery or a termination-protocol exchange
- termination hint summary: ABORT safe via risk

## Participant summary
| Participant | Role | Planned vote | 2nd-phase delivery | Final state | Acked decision | Recovered after reconnect | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| inventory | reserve stock | commit | deliver | prepared | no | no | inventory is prepared and waiting for the final decision |
| risk | fraud screening | abort | deliver | aborted | no | no | risk rejects the transaction before it ever reaches PREPARED |
| billing | capture payment | commit | deliver | prepared | no | no | billing is prepared but never hears the durable ABORT before the crash |

## Termination protocol hints
- Ask whether any peer never reached PREPARED. Here, risk never prepared local work, so the classic termination protocol can safely conclude `ABORT`.
- This is the normal escape hatch when a participant can prove the transaction never reached unanimous PREPARED state.
- If every reachable peer is instead still PREPARED/in doubt, the block remains.

## Trace
1. coordinator starts 2PC for order-6112 with 3 participants
2. coordinator -> inventory: PREPARE
3. inventory: writes PREPARED record and replies YES
4. coordinator -> risk: PREPARE
5. risk: replies NO and requests global abort
6. coordinator -> billing: PREPARE
7. billing: writes PREPARED record and replies YES
8. coordinator writes ABORT decision because at least one participant voted NO
9. coordinator crashes after the durable decision is logged but before all participants hear it
10. some prepared participants still lack the final decision and remain blocked until coordinator recovery or a termination-protocol exchange

## Takeaways
- 2 participants were willing to commit, 1 voted abort, and 0 timed out.
- 2 participants reached PREPARED before the transaction finished.
- 0 participants already know the durable ABORT while other prepared peers remain blocked.
- the durable ABORT decision exists, but no prepared participant has learned it yet; prepared participants stay in doubt until recovery or a termination-protocol exchange
- Final coordinator state: crashed-after-decision.

# Fraud check forces global abort

Inventory is ready, but the risk service votes NO after a fraud signal. The coordinator must abort the whole distributed transaction so no participant commits alone.

## Outcome
- transaction id: `order-1088`
- scenario tags: `abort`, `veto`, `baseline`
- final outcome: `abort`
- durable decision recorded: `yes`
- coordinator crash point: `none`
- coordinator recovery simulated: `no`
- configured decision deliveries before crash: `0`
- successful decision deliveries before crash: `0`

## Participant summary
| Participant | Role | Planned vote | 2nd-phase delivery | Final state | Acked decision | Recovered after reconnect | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| inventory | reserve stock | commit | deliver | aborted | yes | no | items are in stock |
| risk | fraud screening | abort | deliver | aborted | no | no | card fingerprint mismatched historical behavior |
| billing | capture payment | commit | deliver | aborted | yes | no | would have charged if risk had approved |

## Trace
1. coordinator starts 2PC for order-1088 with 3 participants
2. coordinator -> inventory: PREPARE
3. inventory: writes PREPARED record and replies YES
4. coordinator -> risk: PREPARE
5. risk: replies NO and requests global abort
6. coordinator -> billing: PREPARE
7. billing: writes PREPARED record and replies YES
8. coordinator writes ABORT decision because at least one participant voted NO
9. coordinator -> inventory: ABORT
10. inventory: rolls back prepared work and acknowledges ABORT
11. risk: is already safely aborted
12. coordinator -> billing: ABORT
13. billing: rolls back prepared work and acknowledges ABORT
14. transaction resolves as ABORT

## Takeaways
- 2 participants were willing to commit, 1 voted abort, and 0 timed out.
- 2 participants reached PREPARED before the transaction finished.
- 2PC aborts whenever a participant refuses, times out, or recovery cannot prove a durable COMMIT record.
- Final coordinator state: complete.

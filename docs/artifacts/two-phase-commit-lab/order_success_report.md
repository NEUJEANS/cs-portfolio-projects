# Order service happy-path commit

Inventory, billing, and shipping all vote YES, so the coordinator records a durable commit and every participant applies the order in the second phase.

## Outcome
- transaction id: `order-1042`
- final outcome: `commit`
- durable decision recorded: `yes`
- coordinator crash point: `none`
- coordinator recovery simulated: `no`
- configured decision deliveries before crash: `0`
- successful decision deliveries before crash: `0`

## Participant summary
| Participant | Role | Planned vote | 2nd-phase delivery | Final state | Acked decision | Recovered after reconnect | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| inventory | reserve stock | commit | deliver | committed | yes | no | SKU stock is available |
| billing | capture payment | commit | deliver | committed | yes | no | authorization already succeeded |
| shipping | create shipment | commit | deliver | committed | yes | no | carrier label quota is healthy |

## Trace
1. coordinator starts 2PC for order-1042 with 3 participants
2. coordinator -> inventory: PREPARE
3. inventory: writes PREPARED record and replies YES
4. coordinator -> billing: PREPARE
5. billing: writes PREPARED record and replies YES
6. coordinator -> shipping: PREPARE
7. shipping: writes PREPARED record and replies YES
8. coordinator writes COMMIT decision to durable log
9. coordinator -> inventory: COMMIT
10. inventory: commits local work and acknowledges COMMIT
11. coordinator -> billing: COMMIT
12. billing: commits local work and acknowledges COMMIT
13. coordinator -> shipping: COMMIT
14. shipping: commits local work and acknowledges COMMIT
15. transaction resolves as COMMIT

## Takeaways
- 3 participants were willing to commit, 0 voted abort, and 0 timed out.
- 3 participants reached PREPARED before the transaction finished.
- 2PC commits only because every participant voted YES and the coordinator recorded a durable COMMIT decision.
- Final coordinator state: complete.

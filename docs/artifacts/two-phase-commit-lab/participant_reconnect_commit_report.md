# Participant reconnect resolves a missed COMMIT

All participants vote YES and the coordinator durably logs COMMIT, but shipping misses the first second-phase message during a disconnect. After timing out in PREPARED, it reconnects, learns the durable decision, and safely commits.

## Outcome
- transaction id: `order-4099`
- final outcome: `commit`
- durable decision recorded: `yes`
- coordinator crash point: `none`
- coordinator recovery simulated: `no`

## Participant summary
| Participant | Role | Planned vote | 2nd-phase delivery | Final state | Acked decision | Recovered after reconnect | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| inventory | reserve stock | commit | deliver | committed | yes | no | inventory receives the decision on the first broadcast |
| billing | capture payment | commit | deliver | committed | yes | no | billing acknowledges COMMIT immediately |
| shipping | create shipment | commit | miss | committed | yes | yes | a network blip drops the first COMMIT delivery, so shipping reconnects to fetch the durable outcome |

## Trace
1. coordinator starts 2PC for order-4099 with 3 participants
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
14. shipping: misses the first COMMIT delivery while disconnected and stays PREPARED
15. shipping: times out in PREPARED, reconnects, and asks the coordinator to replay the durable decision
16. shipping: reconnects, learns the durable COMMIT decision, commits local work, and acknowledges COMMIT
17. transaction resolves as COMMIT

## Takeaways
- 3 participants were willing to commit, 0 voted abort, and 0 timed out.
- 3 participants reached PREPARED before the transaction finished.
- 1 participant missed the first second-phase delivery, and 1 participant later recovered by reconnecting for the durable decision.
- 2PC commits only because every participant voted YES and the coordinator recorded a durable COMMIT decision.
- Final coordinator state: complete.

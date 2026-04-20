# Recovery replays a durable commit

All participants vote YES, the coordinator durably logs COMMIT, then crashes before everyone hears the outcome. Recovery replays the log and safely finishes phase two.

## Outcome
- transaction id: `order-3050`
- final outcome: `commit`
- durable decision recorded: `yes`
- coordinator crash point: `after-decision-log`
- coordinator recovery simulated: `yes`
- configured decision deliveries before crash: `0`
- successful decision deliveries before crash: `0`

## Participant summary
| Participant | Role | Planned vote | 2nd-phase delivery | Final state | Acked decision | Recovered after reconnect | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| inventory | reserve stock | commit | deliver | committed | yes | no | reservation is prepared before the crash |
| billing | capture payment | commit | deliver | committed | yes | no | prepared payment can commit after recovery |
| shipping | create shipment | commit | deliver | committed | yes | no | shipment creation waits for replayed decision |

## Trace
1. coordinator starts 2PC for order-3050 with 3 participants
2. coordinator -> inventory: PREPARE
3. inventory: writes PREPARED record and replies YES
4. coordinator -> billing: PREPARE
5. billing: writes PREPARED record and replies YES
6. coordinator -> shipping: PREPARE
7. shipping: writes PREPARED record and replies YES
8. coordinator writes COMMIT decision to durable log
9. coordinator crashes after the durable decision is logged but before all participants hear it
10. recovery replays the durable decision log and resumes decision broadcast
11. coordinator -> inventory: COMMIT
12. inventory: commits local work and acknowledges COMMIT
13. coordinator -> billing: COMMIT
14. billing: commits local work and acknowledges COMMIT
15. coordinator -> shipping: COMMIT
16. shipping: commits local work and acknowledges COMMIT
17. transaction resolves as COMMIT

## Takeaways
- 3 participants were willing to commit, 0 voted abort, and 0 timed out.
- 3 participants reached PREPARED before the transaction finished.
- 2PC commits only because every participant voted YES and the coordinator recorded a durable COMMIT decision.
- Final coordinator state: complete.

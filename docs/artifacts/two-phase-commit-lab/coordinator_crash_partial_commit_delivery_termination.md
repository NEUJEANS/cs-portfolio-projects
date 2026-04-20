# Coordinator crash after one COMMIT delivery peer-to-peer termination resolution

All participants vote YES and the coordinator durably logs COMMIT. Inventory hears the second-phase COMMIT first, then the coordinator crashes before billing and shipping hear it. The remaining prepared participants are blocked, but a peer-to-peer termination check can still learn COMMIT from inventory while waiting for recovery.

## Baseline 2PC state
- transaction id: `order-5120`
- baseline outcome: `blocked`
- baseline decision: `commit`
- baseline termination hint: COMMIT visible via inventory

## Peer-to-peer resolution result
- resolution outcome: `commit`
- resolved decision: `commit`
- unresolved participants after peer exchange: `none`

## Participant actions
| Participant | Role | Initial state | Peer query | Evidence | Final state | Resolved |
| --- | --- | --- | --- | --- | --- | --- |
| inventory | reserve stock | committed | answer peer termination requests | already knows the durable COMMIT decision | committed | yes |
| billing | capture payment | prepared | ask inventory for the final decision | inventory already knows the durable COMMIT decision | committed | yes |
| shipping | create shipment | prepared | ask inventory for the final decision | inventory already knows the durable COMMIT decision | committed | yes |

## Resolution trace
1. billing: asks inventory about the missing outcome, learns COMMIT, and finishes as COMMITTED
2. shipping: asks inventory about the missing outcome, learns COMMIT, and finishes as COMMITTED

## Takeaways
- Classic 2PC remains blocking until a PREPARED participant either reaches the coordinator or learns an authoritative fact from a peer.
- This scenario's peer-to-peer termination exchange resolves the blocked participants to `commit` without inventing a brand-new outcome locally.
- Once inventory already knows `COMMIT`, that peer can act as the decisive witness for the remaining PREPARED participants.

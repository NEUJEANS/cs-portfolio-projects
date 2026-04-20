# Coordinator crash before durable decision peer-to-peer termination resolution

Every participant votes YES and enters PREPARED, but the coordinator crashes before it records COMMIT or ABORT. This is the classic blocking case that makes plain 2PC operationally painful.

## Baseline 2PC state
- transaction id: `order-2021`
- baseline outcome: `blocked`
- baseline decision: `none`
- baseline termination hint: wait: all prepared peers are still uncertain

## Peer-to-peer resolution result
- resolution outcome: `still-blocked`
- resolved decision: `none`
- unresolved participants after peer exchange: `inventory, billing, and shipping`

## Participant actions
| Participant | Role | Initial state | Peer query | Evidence | Final state | Resolved |
| --- | --- | --- | --- | --- | --- | --- |
| inventory | reserve stock | prepared | ask peers whether anyone knows the final decision or never reached PREPARED | every reachable peer is still PREPARED/in doubt, so no safe local conclusion exists yet | prepared | no |
| billing | capture payment | prepared | ask peers whether anyone knows the final decision or never reached PREPARED | every reachable peer is still PREPARED/in doubt, so no safe local conclusion exists yet | prepared | no |
| shipping | create shipment | prepared | ask peers whether anyone knows the final decision or never reached PREPARED | every reachable peer is still PREPARED/in doubt, so no safe local conclusion exists yet | prepared | no |

## Resolution trace
1. inventory: asks peers for the final outcome, but everyone reachable is still uncertain, so the participant stays PREPARED
2. billing: asks peers for the final outcome, but everyone reachable is still uncertain, so the participant stays PREPARED
3. shipping: asks peers for the final outcome, but everyone reachable is still uncertain, so the participant stays PREPARED

## Takeaways
- Classic 2PC remains blocking until a PREPARED participant either reaches the coordinator or learns an authoritative fact from a peer.
- The peer check still cannot finish the protocol here because every reachable peer is just as uncertain as the blocked participant.
- When no peer knows COMMIT/ABORT and no peer can prove a missing PREPARED record, plain 2PC stays blocked until coordinator recovery.

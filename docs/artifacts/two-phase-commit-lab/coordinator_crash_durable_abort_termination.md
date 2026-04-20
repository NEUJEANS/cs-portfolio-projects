# Coordinator crash after durable ABORT peer-to-peer termination resolution

Inventory and billing vote YES, but risk votes NO. The coordinator durably logs ABORT and crashes before the prepared YES-voters hear the decision. They are blocked in classic 2PC, but a peer-to-peer termination check can still prove ABORT safely because risk never reached PREPARED.

## Baseline 2PC state
- transaction id: `order-6112`
- baseline outcome: `blocked`
- baseline decision: `abort`
- baseline termination hint: ABORT safe via risk

## Peer-to-peer resolution result
- resolution outcome: `abort`
- resolved decision: `abort`
- unresolved participants after peer exchange: `none`

## Participant actions
| Participant | Role | Initial state | Peer query | Evidence | Final state | Resolved |
| --- | --- | --- | --- | --- | --- | --- |
| inventory | reserve stock | prepared | ask risk whether anyone never reached PREPARED | risk never prepared local work, so ABORT is the only safe outcome | aborted | yes |
| risk | fraud screening | aborted | answer whether local work ever reached PREPARED | never reached PREPARED, so this peer can help prove ABORT | aborted | yes |
| billing | capture payment | prepared | ask risk whether anyone never reached PREPARED | risk never prepared local work, so ABORT is the only safe outcome | aborted | yes |

## Resolution trace
1. inventory: asks risk about PREPARED state, proves ABORT safely, and rolls back local work
2. billing: asks risk about PREPARED state, proves ABORT safely, and rolls back local work

## Takeaways
- Classic 2PC remains blocking until a PREPARED participant either reaches the coordinator or learns an authoritative fact from a peer.
- This scenario's peer-to-peer termination exchange resolves the blocked participants to `abort` without inventing a brand-new outcome locally.
- Seeing that risk never reached PREPARED is enough to conclude `ABORT` safely.

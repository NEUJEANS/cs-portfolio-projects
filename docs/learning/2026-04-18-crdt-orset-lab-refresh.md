# CRDT OR-Set Refresh + Self-Test — 2026-04-18

## Quick refresh
- A state-based CRDT merge must be associative, commutative, and idempotent so replica state converges despite reordering or duplicate deliveries.
- In an OR-Set, each add gets a unique tag; membership depends on whether any non-tombstoned tag remains for that element.
- A remove only tombstones the tags currently observed on that replica, which is why a concurrent/new add can survive later.

## Self-test
1. **Why not model remove as deleting the whole element unconditionally?**  
   Because that would erase concurrent adds the replica never observed and break OR-Set semantics.
2. **What does the tombstone set store here?**  
   The specific add-tags that were observed and removed.
3. **How do you show convergence clearly in a student project?**  
   Run the same scripted scenario across multiple replicas, then print per-replica active tags plus a final converged-membership report.

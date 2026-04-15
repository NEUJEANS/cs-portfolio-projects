# Distributed snapshot concurrent refresh

## Refresher
- A distributed snapshot records process-local state plus messages seen on channels before the first marker arrives on that channel for a given snapshot.
- Concurrent snapshots require namespacing marker handling by snapshot id.
- In a small teaching simulator, the cleanest API is often `snapshot_id -> result` rather than trying to merge all markers into one flat stream.

## Tiny self-test
1. Why do concurrent snapshots need IDs?
   - So processes can distinguish which recording window each marker belongs to.
2. What should stay separate per snapshot?
   - Recorded balances, closed channels, markers seen, and captured in-flight messages.
3. What can stay shared in this repo?
   - The transfer timeline and the underlying simulated bank state.

# Distributed Snapshot Refresh

## Refresher points
- Chandy-Lamport records a process's local state when it first sees a marker for a snapshot.
- After recording local state, the process records incoming-channel messages until it receives a marker on that incoming channel.
- Messages sent after the local state is recorded should not appear in the recorded outgoing channel state for that process.
- A useful sanity check in a bank-transfer simulation is that snapshot balances plus recorded channel money equals total money in the system.

## Self-test
1. If process `B` gets a marker from `A` before it gets one from `C`, which `C -> B` messages belong to channel state?
   - The messages that were already in transit on `C -> B` before `B` received `C`'s marker.
2. Why is an in-flight message sometimes part of the snapshot even if the receiver has not applied it yet?
   - Because the snapshot represents a consistent cut of the distributed execution, not only completed receives.
3. What invariant is easiest to assert in a bank-transfer toy model?
   - Total money in local balances plus in-flight messages stays constant.

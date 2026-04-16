# Distributed Snapshot Lab Learning + Self-Test — 2026-04-16

## Quick refresh
- A Chandy-Lamport snapshot records local process state plus messages that were in transit on channels whose markers have not yet been seen.
- A process crash and a link partition are different failure modes: the process may still be alive even when a specific directed edge is unavailable.
- In a small teaching simulator, making directed channel state explicit is enough to explain blocked marker propagation and why some channels should not be treated like healthy paths.

## Self-test
1. **Why add link failures instead of only process failures?**  
   Because it teaches that communication topology can fail independently of node liveness.
2. **What should a down directed link block here?**  
   New sends, pending deliveries on that edge, and marker propagation along that edge.
3. **Why expose channel state in snapshot output?**  
   So the observed cut is easier to interpret during demos, debugging, and interviews.

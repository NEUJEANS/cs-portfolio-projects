# Chang-Roberts leader election refresh — 2026-04-15

## Quick refresh
- Chang-Roberts runs on a unidirectional logical ring.
- Each initiator injects its own process id as an election message.
- Lower candidate ids are replaced by larger active ids as they circulate.
- When a node receives its own id back, it knows it is the leader.
- A second phase can announce the winner around the ring so every live node learns the leader.

## Self-test
- If node 12 is the highest live id in the ring, any lower candidate is eventually replaced before completing the cycle.
- The algorithm's classic worst-case message cost is quadratic in the number of active nodes.
- Failed nodes should be removed from the active logical ring in this simplified lab before the election starts.

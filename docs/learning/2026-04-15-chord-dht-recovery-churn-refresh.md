# Chord DHT recovery churn refresh

- Timestamp: 2026-04-15 19:44 UTC
- Scope: `projects/chord-dht-lab`

## Quick refresh
- In this simulator, a recovery/rejoin is best modeled as a join of a node that already belonged to the original ring but is currently absent after failure.
- The safest validation rule is: `recover` requires the node to be absent from the current live ring and present in the original baseline ring.
- That keeps the churn event stream explicit and prevents ambiguous cases where `recover` silently behaves like `join` for arbitrary new nodes.

## Self-test
- If `charlie` fails and later returns, use `{"action": "recover", "node": "charlie"}`.
- If `foxtrot` was only introduced by a prior churn `join`, a later return should stay a `join`, not `recover`.

# Link-State Routing Refresh - 2026-04-16

## Quick refresh
- Link-state routing shares topology facts, not whole distance vectors.
- An LSA should include the originating router identity, adjacent links, a freshness marker (sequence), and age.
- Flooding should forward a newly accepted LSA to neighbors except the sender.
- Every router can compute shortest paths independently once the LSDB converges.
- Deterministic tie-breaking matters in tests so equal-cost paths do not flap between runs.

## Self-test
1. Why use sequence numbers?  
   To reject stale or duplicate LSAs and keep the LSDB monotonic.
2. Why is age still needed if sequence numbers exist?  
   To purge old state when a router disappears or stops refreshing advertisements.
3. Why does each router run SPF locally instead of waiting for a central controller?  
   Link-state protocols distribute the same topology database so each router can compute loop-free next hops on its own.
4. What deterministic tie-break did this slice use?  
   Heap ordering by total cost and then lexicographically comparable path tuples.

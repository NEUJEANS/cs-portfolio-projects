# Distance Vector Routing Route Aging Refresh

## Quick refresh
- direct routes should not age out just because a router is silent; learned routes are the ones that become stale when refreshes stop
- once a learned route times out, mark it unreachable (`cost = infinity`, `next_hop = null`) and let that change propagate
- keep the feature optional so existing simulations and tests stay valid

## Self-test
1. If router `C` goes silent in `A-B-C`, should `B -> C` disappear immediately?  
   No. `B` still has a direct link to `C`, so its direct route remains.
2. Which route should age out first in that topology?  
   `A -> C`, because it is learned via `B` and stops being refreshed.
3. What portfolio value does this add?  
   It shows protocol realism beyond static shortest paths: stale state, timers, and reconvergence behavior.

# Distance Vector Routing Route Aging Review — Pass 2

## Focus
Protocol behavior: does a silent-router outage actually age learned routes, or are they dropped immediately?

## Findings
1. Learned routes sourced from a newly silent next hop were disappearing in the first post-outage round.
2. That behavior skipped the intended timeout window, making the feature look like immediate withdrawal instead of realistic stale-route expiration.

## Fixes applied
- Preserved previously learned routes from silent next hops during periodic recomputation until the route timeout logic invalidates them.
- Updated the outage-focused unit test to assert behavior from a converged pre-outage snapshot, which matches the feature goal.

## Verification
- Re-ran the distance-vector test module and manually inspected `simulate-outage` JSON history for `A -> C` aging from cost 2 to infinity after timeout.

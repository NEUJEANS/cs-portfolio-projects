# Distance Vector Routing Route Aging Research

## Goal
Add a realistic stale-route expiration slice to the distance-vector lab without turning it into a full router emulator.

## Notes
- RIP keeps routes fresh with periodic updates; if an update stops arriving, the route becomes invalid after a timeout and is typically advertised as unreachable with metric 16.
- Triggered updates are commonly sent immediately when a route changes state instead of waiting for the next periodic interval.
- Real implementations often also have holddown/flush timers, but the smallest meaningful portfolio slice is route aging + invalidation + triggered propagation.
- Silent-router outage is a good teaching scenario because links can remain in the input graph while learned routes still expire due to missing advertisements.

## Practical slice choice
Implement:
1. optional silent routers that do not advertise,
2. per-route age tracking for learned routes,
3. timeout-driven invalidation to infinity,
4. history output showing age / expiration state.

Skip for now:
- full holddown semantics,
- full flush timer removal,
- protocol-accurate packet/message scheduling.

## References
- Juniper RIP timer docs
- Cisco/community explanations of RIP invalid vs triggered updates
- RIP overview references discussing metric 16 as infinity

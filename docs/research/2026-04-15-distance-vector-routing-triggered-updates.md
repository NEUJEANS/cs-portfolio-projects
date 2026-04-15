# Distance Vector Routing Triggered Updates Research

## Goal
Add an explicit scheduling mode so the lab can contrast coarse periodic full-table exchanges with more event-driven triggered updates.

## Sources
- RFC 2453 (RIP Version 2), especially sections on distance-vector instability, triggered updates, and timers.
- Existing project behavior and prior count-to-infinity slice notes in this repo.

## Takeaways
- Classic RIP sends unsolicited full updates on a fixed cadence (commonly every 30 seconds).
- Triggered updates are sent when routes change instead of waiting for the next periodic cycle.
- Triggered behavior is mainly about propagation schedule, not a different shortest-path algorithm.
- For this portfolio lab, an explicit scheduler is more valuable than emulating wall-clock seconds exactly.

## Slice decision
Model two propagation strategies:
1. `periodic`: every round lets all routers advertise.
2. `triggered`: one router advertises at a time, and only neighbors of changed routers get queued next.

This keeps the simulator deterministic and makes message scheduling visible in the JSON history without turning the project into a packet-level emulator.

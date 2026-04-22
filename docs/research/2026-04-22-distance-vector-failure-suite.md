# Distance Vector Failure Suite Research Note

- Date: 2026-04-22
- Project: `distance-vector-routing-lab`
- Slice: curated multi-scenario failure benchmark suite

## Brief research takeaway
A quick RIP refresher supported expanding the benchmark from one tiny line topology into a richer scenario pack:
- RFC 2453 discusses split horizon and triggered updates as instability mitigations, but not as a guarantee that every larger loop disappears immediately
- split horizon and poison reverse are strongest on the small mutual-deception cases they were designed for, while larger rings can still bounce bad news around before the network settles
- triggered updates reduce delay after a topology change, but they still propagate whatever routing knowledge the routers currently have, good or bad

## Sources checked
- RFC 2453 (RIP Version 2), especially the split-horizon and triggered-update sections

## Decision for this slice
Add a built-in failure benchmark suite with several named scenarios instead of only the `A-B-C` loop, so the project can compare:
- a pure count-to-infinity failure
- an alternate-path detour
- a larger ring where mitigation is helpful but not magical
- a longer bypass path that remains reachable after the failure

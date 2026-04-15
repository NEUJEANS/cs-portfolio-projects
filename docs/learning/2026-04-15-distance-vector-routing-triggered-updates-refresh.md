# Distance Vector Routing Triggered Updates Refresh

## Quick refresh
- Distance-vector routing is still Bellman-Ford at heart; the interesting systems behavior comes from *when* advertisements are sent.
- Periodic updates approximate a fixed timer tick.
- Triggered updates approximate a route-change flag causing near-immediate propagation.
- Split horizon / poison reverse change what a router advertises, while periodic / triggered change when it advertises.

## Self-test
1. **Question:** Do triggered updates change the final shortest paths in a stable topology?
   **Answer:** No. They should change propagation schedule and intermediate history, not the converged result.
2. **Question:** What extra visibility should the simulator expose for this slice?
   **Answer:** Which router(s) were active each round so the schedule is inspectable.
3. **Question:** Why not model real-time timers in seconds yet?
   **Answer:** Round-based deterministic scheduling is simpler to test and still teaches the key protocol idea.

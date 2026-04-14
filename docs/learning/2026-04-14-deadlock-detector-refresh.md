# deadlock-detector-lab refresh and self-test

## Quick refresh
- A **wait-for graph** has one node per process and an edge `P -> Q` when `P` is waiting for a resource held by `Q`.
- In the single-instance model, a directed cycle implies deadlock.
- In the multi-instance model, a convenient detector tracks a `work` vector initialized from `available` resources and repeatedly marks a process finishable when `request[process] <= work`; when it finishes, its allocation is released back into `work`.
- Processes left unfinished after no more progress are the deadlocked candidates.

## Self-test
1. If `P1 -> P2 -> P3 -> P1`, is the wait-for graph deadlocked? **Yes, there is a directed cycle.**
2. If `available = {printer: 1}`, `request[P1] = {printer: 1}`, and no one currently holds the printer, can `P1` finish? **Yes; request is satisfiable immediately.**
3. Why keep a blocking-explanation map? **Because interview-quality tooling should show which resource shortages prevent completion, not just a boolean result.**

## Implementation choices for this slice
- use DFS with an explicit recursion stack to report one concrete cycle in the wait-for graph
- use deterministic ordering so JSON output and tests stay stable
- surface blocking details for unfinished processes in allocation analysis

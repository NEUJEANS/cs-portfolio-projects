# deadlock-detector-lab Banker request gallery notes

## Why this slice
The deadlock-detector lab already showed one safe request trial well, but the avoidance story still needed a one-glance contrast between a granted request and a denied unsafe request.

## Brief research refresh
- Banker's algorithm only grants a request after a trial allocation still leaves at least one safe sequence.
- A denied request is not necessarily an immediate deadlock, but it does mean the simulated post-request state is unsafe and should be rolled back.
- The most portfolio-friendly comparison is not just granted vs denied. It is whether the trial still leaves any runnable process and what blocking shortages remain.

## Scope decision
- reuse the existing request-trace renderer instead of building a second custom diagram system
- add one comparison command that can take multiple request JSON files and produce recruiter-friendly Markdown/HTML outputs
- commit one deterministic unsafe sample request plus a side-by-side gallery artifact so the contrast is easy to screenshot

## Sources checked
- web search refresh on Banker's algorithm safe-state rule and request-grant workflow (safe sequence must still exist after the simulated allocation)
- existing project traces and tests, which already included one unsafe request example worth promoting into committed artifacts

# CPU Scheduler Simulator Research — 2026-04-14

## Scope for this slice
Build a portfolio-friendly simulator that models classic CPU scheduling algorithms with reproducible metrics and text-based timeline output.

## Reference concepts reviewed
- CPU scheduling fundamentals and common metrics from standard operating-systems references.
- Core metrics to report consistently:
  - **completion time**: when a process finishes
  - **turnaround time** = completion - arrival
  - **waiting time** = turnaround - burst
  - **response time** = first run start - arrival
- Initial algorithm set chosen for this slice:
  - **FCFS**: baseline non-preemptive scheduler
  - **SJF (non-preemptive)**: shortest available job first, ties broken deterministically
  - **Round Robin**: preemptive fairness with configurable quantum
- Useful output for a portfolio project:
  - per-process metrics table
  - average metrics summary
  - Gantt/timeline style execution trace
  - JSON export option for programmatic checks

## Design choices for implementation
- Use a small Python CLI to keep the project easy to run.
- Accept workloads from JSON files and from inline examples in tests.
- Keep tie-breaking deterministic using arrival time then process id.
- Represent the timeline as slices like `[start,end): pid` so tests can validate scheduling behavior.
- Include idle intervals in the timeline for realism.

## Vertical slice target
- model processes with arrival and burst times
- simulate FCFS, SJF, and Round Robin
- compute per-process and average metrics
- print a human-readable report and JSON output
- cover algorithm behavior with unit tests

## Next useful extensions
- SRTF / priority scheduling
- context-switch overhead
- workload generators
- ASCII charts or SVG export

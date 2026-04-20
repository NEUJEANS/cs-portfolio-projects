# Dependency graph planner strategy-comparison slice research — 2026-04-20

## Brief research
- No extra external web research was needed for this slice because the planner already had deterministic worker-limited scheduling plus a clear README/checklist follow-up: compare ready-queue heuristics on the same DAG.
- The missing portfolio value was not a new algorithm family; it was a concrete demonstration that scheduler policy can change the makespan even when the DAG and worker cap stay fixed.
- A good showcase graph needs one short critical-path seed task competing against longer non-critical tasks so `critical-first` can pull the critical chain forward while `fifo` or `longest-processing-time` can accidentally starve it.

## Slice decision
Add selectable scheduling strategies to `schedule`/`report` and commit a dedicated `strategy_graph.json` example that shows:
- `critical-first` finishing earlier under a `2`-worker cap
- `fifo` and `longest-processing-time` delaying the short critical seed behind long non-critical work
- one recruiter-friendly report with linked per-strategy schedule JSON snapshots for direct comparison

Why this is the right next slice:
- it completes the exact README/checklist follow-up left after multi-capacity comparison support shipped
- it makes the project more interview-friendly by turning an abstract heuristic discussion into a reproducible artifact bundle
- it stays resumable because the implementation reuses the existing worker-limited report and artifact pipeline instead of creating a parallel export path

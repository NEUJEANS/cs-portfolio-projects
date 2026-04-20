# Dependency graph planner strategy-comparison refresh — 2026-04-20

## Short refresh
- List scheduling is still deterministic as long as the ready queue has a stable priority rule.
- `critical-first` is a practical heuristic for DAG demos because low-slack tasks are the ones most likely to stretch the makespan when delayed.
- `fifo` is easy to explain but can punish short critical-path work if long non-critical tasks happened to enter the queue first.
- `longest-processing-time` can improve packing on some workloads, but on dependency graphs it can still lose badly if it ignores criticality.

## Self-test
1. Why use a dedicated strategy graph instead of the existing sample graph?
   - Because the original sample keeps the same makespan across the built-in strategies, so it does not visibly teach the heuristic tradeoff.
2. What should happen on the strategy graph at `2` workers?
   - `critical-first` should finish in `13`, while `fifo` and `longest-processing-time` should both finish in `16` by delaying `core-seed`.
3. Why keep the strategy names machine-readable in the report and JSON artifacts?
   - So the CLI flags, committed artifact filenames, and regression assertions all stay aligned and reproducible.

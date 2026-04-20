# Dependency graph planner benchmark-suite slice research — 2026-04-20

## Brief research
- No extra external web research was needed for this slice because the scheduler, report writer, and showcase manifests were already in place; the missing value was a batch runner that could replay them together.
- The portfolio gap after the strategy/resource slices was comparison at the suite level: one manifest showed a heuristic win, another showed a resource bottleneck tie, and another showed an override changing the best strategy.
- A strong benchmark suite should therefore mix:
  - an easy baseline where all strategies tie
  - a graph where `critical-first` wins clearly
  - a resource-constrained case where tie-breaking matters even when makespan does not
  - an override scenario where changing capacities flips the preferred strategy

## Slice decision
Add a `benchmark` command plus a committed `portfolio_benchmark_suite.json` file that:
- loads relative graph paths safely from the suite directory
- replays one or more selected strategies per scenario
- supports inline resource-capacity overrides for scenario-local experiments
- emits a recruiter-friendly Markdown scoreboard alongside JSON output for tests and scripting

Why this is the right next slice:
- it completes the exact next-step note left by the multi-resource wrap-up
- it turns the existing isolated demos into a coherent story about scheduler behavior across workloads
- it stays resumable because the suite file can grow scenario-by-scenario without changing the core manifest format

# CPU Scheduler Simulator Learning Note — 2026-04-21 Benchmark Scorecards Self-Test

## Quick refresh
- The benchmark pack already had trustworthy metrics, but it still read like a raw dump. A recruiter-facing artifact needs a quicker answer to "when does each scheduler win?".
- Win counts alone are useful but not very visual. A heatmap makes the same evidence scannable in a screenshot without throwing away exact counts.
- For this repo, a compact case-study layer is more valuable than adding another scheduler immediately because the current pack already has enough algorithm variety to tell a strong story.

## Self-test
1. **Q:** Why add scorecards instead of just another benchmark table?  
   **A:** Because the weak spot was interpretation, not raw data collection. Scorecards turn the benchmark into an explanation artifact.

2. **Q:** Why use win-rate heatmap cells like `3/6` plus `%` instead of only color?  
   **A:** Because the artifact should still be evidence-first and readable in Markdown/HTML contexts, not only visually suggestive.

3. **Q:** Why keep the heatmap focused on headline goals instead of every available metric?  
   **A:** Because the portfolio audience needs a concise summary first. Too many columns would make the screenshot noisier than the current table.

## Pre-edit baseline check
- reran `python3 projects/cpu-scheduler-simulator/scheduler.py benchmark --help`
- reran `python3 projects/cpu-scheduler-simulator/scheduler.py benchmark --benchmark-family portfolio-batch --quantum 2 --aging-interval 2 --mlfq-quantums 2,4,8 --mlfq-boost-interval 12 --context-switch-cost 1 --markdown-out /tmp/cpu-benchmark-baseline.md`
- confirmed the benchmark flow was healthy before editing, so any regressions would be attributable to the new scorecard and heatmap layer

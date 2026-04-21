# CPU Scheduler Simulator Self-Test — 2026-04-21 MLFQ Tuning Pack Slice

## Quick refresh
- Q: Why add MLFQ tuning packs only to compare and benchmark mode?
  - A: Because the feature is about side-by-side policy analysis. Single-run mode should stay simple and backwards compatible.
- Q: What does the `interactive` ladder try to optimize?
  - A: Faster first response, using a shorter top-queue quantum plus more frequent boosts.
- Q: What does the `throughput` ladder give up to reduce churn?
  - A: It accepts slower response and fairness in exchange for fewer context switches and better batch-heavy throughput.
- Q: Why keep `balanced` in the pack if it matches the old default?
  - A: It anchors the comparison so the tuning story shows how aggressive and conservative ladders move away from the baseline.

## Self-check commands used
- `python3 projects/cpu-scheduler-simulator/scheduler.py benchmark --benchmark-family portfolio-batch --algorithms srtf rr mlfq --quantum 2 --context-switch-cost 1 --mlfq-variant-pack portfolio --output-dir docs/artifacts/cpu-scheduler-simulator/mlfq-tuning-pack`
- deterministic rerun `cmp` checks for benchmark summary Markdown/HTML/JSON/SVG plus `interactive-bursts` compare artifacts

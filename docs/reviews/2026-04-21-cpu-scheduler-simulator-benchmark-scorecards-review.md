# CPU Scheduler Simulator Benchmark Scorecards Review Log

## Pass 1, scorecard fallback audit
- Issue found: algorithms with no outright benchmark-goal wins, especially RR, produced awkward scorecard headlines like `fairness 0/6`, which made the new storytelling layer look broken instead of informative.
- Fix: add a fallback that chooses the strongest relative goal ranks when an algorithm has no outright goal wins, and phrase the headline as a near-miss summary instead of a fake win summary.

## Pass 2, distinctive-strength audit
- Issue found: ranking scorecard goals by raw win counts overemphasized universal tie-heavy goals such as throughput and low overhead, so SJF initially hid its more distinctive turnaround and waiting strengths.
- Fix: compute per-goal fractional points from scenario tie splits and use those to rank scorecard goals before falling back to raw win rates, so the cards favor differentiating strengths instead of generic shared ties.

## Pass 3, documentation and artifact audit
- Issue found: the README and benchmark story still described richer scorecards/heatmaps as future work, which contradicted the shipped slice and weakened the portfolio presentation.
- Fix: refresh the README and benchmark bundle wording so the new scorecards plus `benchmark-heatmap.svg` are presented as first-class committed artifacts, then rerun the benchmark bundle and deterministic `cmp` checks.

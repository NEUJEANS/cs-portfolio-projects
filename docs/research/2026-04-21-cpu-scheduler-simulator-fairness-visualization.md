# CPU Scheduler Simulator Research — 2026-04-21 Fairness and Slowdown Visualization

## Why this slice
The scheduler lab already had aggregate comparison dashboards, but they still flattened away the per-process story. A recruiter or student could see which algorithm won on average without seeing whether one unlucky process absorbed most of the pain.

## Brief refresh
- Turnaround-based slowdown (`turnaround / burst`) is a compact way to normalize how expensive the schedule felt for short and long jobs.
- Waiting-time spread and slowdown spread are better fairness storytelling tools than a single winner-only table because they show whether one process paid a disproportionate cost.
- For this project, a simple per-process dashboard is more useful than a more abstract fairness score because it stays inspectable and screenshot-friendly.

## Modeling choice for this slice
- Keep the existing aggregate comparison table, but add explicit slowdown/fairness summaries beside it.
- Include per-process experience rows in the compare payload so Markdown, HTML, JSON, and SVG outputs all share the same source data.
- Add a deterministic SVG fairness dashboard that plots slowdown and waiting per process for each algorithm, making uneven tails visible in one artifact.
- Prefer concrete metrics such as average slowdown, worst slowdown, and slowdown standard deviation over a single opaque fairness number.

## What this should improve
- makes scheduler tradeoffs easier to explain in interviews and screenshots
- highlights starvation-like tails without requiring manual JSON inspection
- gives the project a more portfolio-ready visual artifact than text tables alone

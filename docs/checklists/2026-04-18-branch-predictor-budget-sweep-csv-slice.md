# 2026-04-18 branch-predictor budget-sweep CSV slice checklist

- [x] pick `branch-predictor-lab` again because the previous wrap-up explicitly called out CSV/export-friendly budget-sweep output as the next missing artifact
- [x] no extra web research was needed because this slice extends the existing branch-predictor CLI/report pipeline rather than introducing a new architecture concept
- [x] no separate language/tool refresh was needed beyond a quick local check of the current `budget-sweep` CLI payload, writer helpers, and test coverage patterns
- [x] update the main project checklist so the completed portfolio slices stay accurate and the next follow-up remains visible
- [x] add a reusable CSV export path for `budget-sweep` and thread it through CLI outputs / JSON metadata
- [x] regenerate the committed budget-sweep Markdown / SVG / CSV artifacts so docs match the shipped CLI behavior
- [x] extend focused tests for renderer output and `--csv-out` CLI coverage
- [x] review the slice at least 3 times and fix issues found
- [x] run repo tests plus focused budget-sweep smoke checks, including a tiny-budget edge case
- [x] run a secret scan before push
- [x] commit, push, and append the final wrap-up with commit hash and next step

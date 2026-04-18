# 2026-04-18 branch-predictor dynamic gshare aliasing slice checklist

- [x] pick `branch-predictor-lab` because the sweep flow was already shipped and the next unfinished architecture slice was dynamic gshare alias visibility
- [x] do a short local branch-predictor refresh by tracing how `GSharePredictor._index()` mixes `(pc >> 2)` with the live global history register
- [x] add a dynamic gshare alias-summary path that groups collisions by live index plus `history_before` context
- [x] thread the new summary through compare JSON/Markdown/SVG output and the sweep report payload
- [x] extend tests for the new summary, compare JSON payload, and committed report rendering hooks
- [x] regenerate committed branch-predictor artifacts so the gallery matches the shipped compare output
- [x] review the slice at least 3 times and fix issues found
- [x] run repo tests plus focused compare/sweep smoke checks
- [x] run a secret scan before push

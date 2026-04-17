# 2026-04-17 branch-predictor aliasing slice checklist

- [x] pick `branch-predictor-lab` as the next weak spot because the README still listed aliasing-focused follow-up work
- [x] capture short branch-predictor aliasing research notes for the slice
- [x] do a short indexing self-test to confirm which PCs collide at table size 16 vs 32
- [x] add an alias-focused synthetic workload that intentionally creates conflicting PC-index collisions
- [x] add compare-output alias summaries that explain the collision buckets in JSON/Markdown/SVG-facing reports
- [x] extend tests for the new workload and for table-size improvement behavior
- [x] generate committed alias-thrash artifacts for the branch-predictor gallery
- [x] review the slice at least 3 times and fix issues found
- [x] run repo tests plus a focused branch-predictor CLI smoke test
- [x] run a secret scan before push

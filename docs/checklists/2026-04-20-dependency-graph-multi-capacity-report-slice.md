# 2026-04-20 Dependency Graph Multi-Capacity Report Slice Checklist

- [x] confirm repo branch/remote state and fetch before editing
- [x] continue the unfinished dependency-graph report slice on top of the locally modified planner file
- [x] reuse the existing 2026-04-19 worker-limited scheduling/report-export notes; no extra web research was needed for this incremental comparison feature
- [x] refresh the expected sample-graph makespans by hand for 1-worker, 2-worker, and 3-worker runs before coding
- [x] implement repeatable `--compare-worker-limit` support for report output plus multi-schedule JSON artifact export
- [x] expand regression coverage for comparison tables, multi-artifact links, deduped comparison limits, and compare-flag validation
- [x] refresh the project README and committed artifact examples for the new comparison workflow
- [x] regenerate non-empty sample comparison artifacts from the checked-in sample graph
- [x] review the slice at least three times and fix the issues found
- [ ] next: compare multiple scheduling heuristics so the report can tell a stronger tradeoff story than worker-cap changes alone

# 2026-04-20 Dependency Graph Renewable Resource-Class Slice Checklist

- [x] confirm repo branch/remote state and fetch before editing
- [x] continue from the locally modified planner file without discarding in-progress work
- [x] capture a brief research note on RCPSP / renewable resource-capacity terminology
- [x] refresh the expected `resource_graph.json` makespans for `gpu=1` and `gpu=2`
- [x] implement manifest-backed `resource_capacities` plus repeatable `--resource-capacity class=count` overrides
- [x] extend recruiter-friendly reports with resource labels, slot assignments, and resource-utilization summaries
- [x] add regression coverage for resource-constrained scheduling, overrides, and CLI validation
- [x] refresh the project README and committed artifact examples for the new resource-constrained workflow
- [x] regenerate non-empty resource-constrained artifacts from a checked-in showcase manifest
- [x] review the slice at least three times and fix the issues found
- [x] run secret scan before push
- [ ] next: support multi-resource demand vectors or richer benchmark suites so the scheduler story goes beyond single-class bottlenecks

# union-find-network-lab Checklist

- [x] brief DSU research recorded
- [x] short Python/data-structure refresh and self-test recorded
- [x] scaffold project files and README
- [x] implement union by rank + path compression
- [x] add component summaries, cycle detection, and stats
- [x] add scriptable CLI workflow and sample operations
- [x] add automated tests for connectivity, cycles, stats, and CLI output
- [x] benchmark mode and CSV edge import for realistic datasets
- [x] export sample benchmark artifacts for README/blog/chart workflows
- [x] render time-series charts from benchmark or CSV snapshot artifacts in a future slice

## SVG chart artifact slice (2026-04-15 13:00 UTC run)
- [x] confirm repo sync before editing
- [x] pick `union-find-network-lab` as the next unfinished project because chart rendering was still only a future idea
- [x] skip external web research because standalone SVG generation is a direct extension of the existing committed artifact workflow
- [x] do a short Python SVG/string-formatting refresh and self-test
- [x] update checklist/docs so the slice is resumable
- [x] add SVG chart rendering for benchmark-series throughput artifacts
- [x] add SVG chart rendering for CSV-import snapshot growth artifacts
- [x] add `--chart-input` support so checked-in JSON/CSV artifacts can be re-rendered without rerunning workloads
- [x] commit sample SVG artifacts and refresh README usage/examples
- [x] expand automated coverage for chart helpers and CLI export flows
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Next slice candidates
- [ ] compare union-find throughput against BFS/DFS recomputation on the same workloads
- [ ] add multi-series chart output so component-count and throughput curves can share one artifact
- [ ] add a tiny README/chart refresh helper for static portfolio publishing

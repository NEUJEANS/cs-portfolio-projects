# mini-mapreduce-lab checklist

## Completed slices
- [x] pick a portfolio-worthy distributed-systems-inspired slice
- [x] define a minimal local MapReduce execution model
- [x] implement built-in text and JSONL jobs
- [x] document usage and future improvements
- [x] add automated tests for pipeline behavior and CLI output
- [x] complete initial 3 review passes and log fixes

## Reducer partitioning slice (2026-04-14 20:49 UTC run)
- [x] confirm repo sync before editing
- [x] refresh partitioner/reducer-skew concepts from existing notes
- [x] add stable reducer bucket partitioning to the execution pipeline
- [x] expose reducer count and reducer stats in CLI/JSON output
- [x] extend tests for deterministic partitioning and CLI validation
- [x] update README with skew-focused usage and talking points
- [x] run tests and 3 review passes

## Synthetic benchmark slice (2026-04-14 21:00 UTC run)
- [x] confirm repo sync before editing
- [x] refresh Python perf-counter and deterministic fixture patterns
- [x] add a synthetic benchmark command for balanced vs skewed wordcount workloads
- [x] report per-reducer-count elapsed time and skew metrics in JSON output
- [x] extend project and repo-level tests for benchmark behavior
- [x] update README with benchmark usage and interview framing
- [x] run tests and 3 review passes
- [ ] consider external mapper/reducer plugin support in a future run

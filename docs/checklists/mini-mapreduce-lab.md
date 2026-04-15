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

## External plugin slice (2026-04-15 02:38 UTC run)
- [x] confirm repo sync before editing
- [x] do brief Python `importlib` research for safe file-based plugin loading
- [x] refresh mapper/reducer callable validation and dynamic import constraints
- [x] add plugin job support with local file loading and validation
- [x] ship an example max-score plugin for portfolio demos
- [x] extend project and repo-level tests for plugin execution and failure modes
- [x] update README with plugin contract and CLI examples
- [x] run tests and 3 review passes
- [ ] consider package-based plugin discovery or non-integer aggregator outputs in a future run

## Importable module plugin slice (2026-04-15 03:00 UTC run)
- [x] confirm repo sync before editing
- [x] refresh `importlib.import_module` loading flow and module-resolution constraints
- [x] extend plugin loading so jobs can come from importable Python modules as well as file paths
- [x] add programmatic and CLI tests for package/module plugin execution
- [x] update README and notes with module-based plugin usage
- [x] run tests and 3 review passes
- [ ] consider typed non-integer reducer outputs or plugin discovery registries in a future run

## Typed plugin output slice (2026-04-15 07:09 UTC run)
- [x] confirm repo sync before editing
- [x] do brief research on JSON-safe reducer output shapes for lightweight MapReduce demos
- [x] do short Python JSON/type-validation refresh and self-test
- [x] update checklist/docs so the slice is resumable
- [x] extend plugin jobs to support JSON-serializable non-integer intermediate and final reducer outputs
- [x] add an average-score example plugin that uses structured combiner state and float reducer output
- [x] extend project and repo-level tests for structured plugin values, deterministic ordering, and JSON validation failures
- [x] run tests and 3 review passes
- [ ] consider CSV benchmark export or reducer heatmap visualization in a future run


## Benchmark CSV export slice (2026-04-15 07:19 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the existing project docs/tests already define the benchmark contract clearly
- [x] do a short Python `csv` refresh and self-test by defining a deterministic header/row contract before coding
- [x] update checklist/docs so the slice is resumable
- [x] add optional benchmark CSV export alongside the existing JSON export
- [x] extend project and repo-level tests for programmatic CSV rendering and CLI file output
- [x] run tests and 3 review passes
- [x] consider shard-by-reducer heatmap export in a future run

## Benchmark heatmap export slice (2026-04-15 09:19 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the reducer-skew follow-up was already scoped in the project notes
- [x] do a short Python `csv.DictWriter` and shard-summary refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add shard-to-reducer heatmap export rows for benchmark runs
- [x] include heatmap data in the benchmark JSON payload and optional CSV file output
- [x] extend project and repo-level tests for deterministic heatmap rendering and CLI file output
- [x] run tests and 3 review passes
- [ ] consider HTML/Markdown chart generation from heatmap rows in a future run

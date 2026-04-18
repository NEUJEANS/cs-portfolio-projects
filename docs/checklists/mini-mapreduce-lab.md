# mini-mapreduce-lab checklist

## Completed slices
- [x] pick a portfolio-worthy distributed-systems-inspired slice
- [x] define a minimal local MapReduce execution model
- [x] implement built-in text and JSONL jobs
- [x] document usage and future improvements
- [x] add automated tests for pipeline behavior and CLI output
- [x] complete initial 3 review passes and log fixes

## Release comparison slice (2026-04-18 00:34 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the release-comparison follow-up is already scoped in the local README/checklist and recent wrap-ups
- [x] do a short Python snapshot-diff and dataclass-loading refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add a `compare-plugin-releases` command that compares two saved plugin-inspection/catalog snapshots
- [x] render Markdown and HTML release-comparison pages with added/removed/changed plugin summaries
- [x] extend the docs index so release-comparison bundles are discoverable next to catalogs/diffs/reports
- [x] extend project-level and repo-level tests for snapshot loading, CLI output, and docs-index discovery
- [x] generate a committed historical release-comparison artifact for the mini-mapreduce docs bundle
- [x] run tests and 3 review passes
- [ ] run secret scan before push
- [ ] commit, push, and add wrap-up

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

## Benchmark Markdown report slice (2026-04-15 10:29 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the benchmark export follow-up was already scoped in the project notes
- [x] do a short Python Markdown-generation and summary-stat refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add benchmark Markdown report export with timing table and shard-to-reducer load summaries
- [x] extend project and repo-level tests for deterministic report rendering and CLI file output
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider HTML chart artifact output in a future run


## Benchmark HTML report slice (2026-04-15 11:19 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the benchmark-export follow-up was already scoped in the project README/checklist
- [x] do a short Python `html.escape` and inline-heatmap rendering refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add standalone HTML benchmark report export with timing summary and colorized shard-to-reducer heatmap tables
- [x] extend project and repo-level tests for programmatic HTML rendering and CLI file output
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider embedded SVG charts or plugin benchmark scenarios in a future run

## SVG chart HTML report slice (2026-04-15 13:29 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the existing benchmark artifact docs already scoped the charting follow-up clearly
- [x] do a short SVG coordinate-scaling and `viewBox` refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add inline SVG timing and reducer-load charts to the standalone HTML report export
- [x] extend project and repo-level tests for SVG rendering and CLI HTML output
- [x] run tests and 3 review passes
- [ ] consider plugin-specific benchmark scenarios in a future run

## Plugin benchmark scenarios slice (2026-04-15 15:05 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the benchmark/report follow-up was already scoped in the existing README and checklist
- [x] do a short Python synthetic-fixture and benchmark-contract refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add plugin benchmark support with deterministic balanced and skewed score datasets
- [x] include benchmark job/plugin metadata in JSON, CSV, Markdown, HTML, and heatmap artifacts
- [x] extend project and repo-level tests for programmatic and CLI plugin benchmark flows
- [x] run tests and 3 review passes
- [x] consider multiple plugin benchmark dataset families or plugin-defined benchmark generators in a future run

## Plugin-defined benchmark generator slice (2026-04-15 15:21 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the project README/checklist
- [x] do a short Python callable-contract and deterministic-fixture refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] let plugins optionally define benchmark input generators for plugin benchmark mode
- [x] wire the average-score example plugin to emit domain-shaped balanced/skewed benchmark fixtures
- [x] extend project and repo-level tests for custom generator success and invalid generator failures
- [x] run tests and 3 review passes
- [x] consider multiple domain-specific dataset families per plugin beyond the basic balanced/skewed hook

## Plugin dataset-family benchmark slice (2026-04-15 15:41 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the open follow-up was already clearly scoped in the README/checklist
- [x] do a short Python callable-signature and backward-compat refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add benchmark dataset-family support to the runner and emitted benchmark artifacts
- [x] extend the average-score plugin with multiple named dataset families (`default`, `exam-cram`, `project-week`)
- [x] extend project and repo-level tests for programmatic and CLI dataset-family benchmark flows
- [x] run tests and 3 review passes
- [ ] consider surfacing supported dataset families automatically in CLI help/report output


## Plugin dataset-family discovery slice (2026-04-15 16:42 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python metadata-validation and backward-compatible plugin-contract refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] let plugins advertise supported benchmark dataset families with validation in the runner
- [x] surface plugin dataset-family metadata in benchmark JSON/Markdown/HTML artifacts and clearer CLI validation errors
- [x] extend project and repo-level tests for metadata rendering and invalid-family failures
- [x] run tests and 3 review passes
- [ ] consider exposing plugin dataset-family metadata in generated CSV summaries or a dedicated inspect subcommand in a future run


## Plugin inspection command slice (2026-04-15 17:22 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python callable-introspection and JSON metadata refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add an `inspect-plugin` command that reports plugin hook names and supported dataset families as JSON
- [x] extend project and repo-level tests for programmatic inspection and CLI JSON output
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] surface inspection metadata in benchmark CSV summaries in a future run

## CSV inspection metadata slice (2026-04-15 18:02 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python `csv.DictWriter` quoting/metadata refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add plugin inspection metadata fields to benchmark JSON/CSV result objects without regressing built-in jobs
- [x] extend project and repo-level tests for plugin metadata rendering in CSV and JSON artifacts
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] surface a dedicated `inspect-plugin --csv-output` artifact in a future run

## Inspect-plugin CSV artifact slice (2026-04-15 18:12 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python `csv.DictWriter` single-row export refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add `inspect-plugin --csv-output` for one-row plugin metadata snapshots
- [x] extend project and repo-level tests for programmatic CSV rendering and CLI dual-output behavior
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider metadata diff tooling or multi-plugin inspection batches in a future run

## Multi-plugin inspection batch slice (2026-04-15 20:52 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python argparse `action="append"` and CSV row-batch refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] extend `inspect-plugin` so repeated `--plugin` flags produce batch JSON/CSV inspection artifacts
- [x] keep single-plugin JSON output backward compatible while adding multi-plugin batch output
- [x] extend project and repo-level tests for programmatic batching plus CLI JSON/CSV batch artifacts
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider plugin metadata diff views once batch snapshots are stable

## Plugin metadata diff slice (2026-04-15 21:42 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python dataclass diff-payload and CLI-flag refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add adjacent plugin metadata diff output for batched `inspect-plugin` runs via `--diff`
- [x] keep existing single-plugin JSON and batch CSV inspection flows backward compatible
- [x] extend project-level and repo-level tests for programmatic diffing plus CLI JSON diff artifacts
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider Markdown/HTML rendering for inspection diffs in a future run


## Inspection diff report slice (2026-04-15 23:12 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python Markdown/HTML report rendering refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add Markdown and HTML artifact export for diff-aware `inspect-plugin` batches
- [x] extend project-level and repo-level tests for programmatic and CLI inspection report output
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider richer inspection summaries such as signatures/docstring excerpts in a future run

## Inspection signatures/doc summaries slice (2026-04-16 02:21 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python `inspect.signature` and module-docstring refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] extend `inspect-plugin` JSON/CSV/Markdown/HTML artifacts with hook signatures and a concise module doc summary
- [x] add concise module docstrings to the built-in example plugins so inspection reports show reviewer-friendly summaries
- [x] extend project-level and repo-level tests for programmatic and CLI inspection artifacts with the richer metadata
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider surfacing per-hook docstring excerpts or source line numbers in a future run

## Inspection hook doc/source metadata slice (2026-04-16 02:47 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python `inspect.getdoc` / `inspect.getsourcelines` refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] extend `inspect-plugin` JSON/CSV/Markdown/HTML artifacts with per-hook doc summaries and source line numbers
- [x] add concise function docstrings to the bundled example plugins so inspection artifacts show reviewer-friendly hook descriptions
- [x] extend project-level and repo-level tests for richer inspection metadata and missing-hook `None` handling
- [x] run tests and 3 review passes
- [ ] consider adding source-code excerpt output or file-anchor links in a future run

## Inspection source excerpt slice (2026-04-16 03:46 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python `inspect.getsourcelines` / file-anchor refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] extend `inspect-plugin` JSON/CSV/Markdown/HTML artifacts with hook source anchors and source excerpts where appropriate
- [x] extend project-level and repo-level tests for richer inspection metadata and report rendering
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider file:// or GitHub blob links for published inspection reports in a future run
- [x] consider repository commit-SHA pinned source links for archival inspection artifacts in a future run

## GitHub source links slice (2026-04-16 05:21 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short git remote / GitHub blob-link refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] extend `inspect-plugin` JSON/CSV/Markdown/HTML artifacts with branch-aware GitHub source URLs when the plugin lives inside a GitHub-backed repo
- [x] extend project-level and repo-level tests for richer inspection metadata and rendered source links
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Commit-pinned inspection links slice (2026-04-16 06:31 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short git `rev-parse HEAD` / archival-link refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] extend `inspect-plugin` JSON/CSV/Markdown/HTML artifacts with repository commit SHAs and commit-pinned GitHub source URLs
- [x] extend project-level and repo-level tests for commit-pinned inspection metadata and rendered report links
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider repository-level inspection index pages or release-to-release comparison artifacts in a future run

## Plugin catalog discovery slice (2026-04-16 07:01 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python `Path.rglob` / glob-filter refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add a `catalog-plugins` command that auto-discovers bundled plugins and emits the same JSON/CSV/Markdown/HTML inspection artifacts
- [x] extend project-level and repo-level tests for plugin discovery, catalog output, and empty-match validation
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider richer catalog landing pages such as per-plugin badges or docs-site navigation sidebars in a future run

## Catalog quick-link landing page slice (2026-04-16 08:01 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the landing-page follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python string-slug and HTML badge rendering refresh/self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add quick-link landing cards plus badge summaries to the catalog Markdown/HTML outputs so reviewers can jump straight to each plugin section
- [x] keep the existing JSON/CSV inspection payloads backward compatible while linking summary rows to per-plugin source sections
- [x] extend project-level and repo-level tests for quick-link anchors and badge rendering
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider generating dedicated per-plugin docs pages from the catalog in a future run

## JSON benchmark families slice (2026-04-16 08:24 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] do brief local research on realistic JSON/event benchmark families
- [x] do a short deterministic JSON fixture refresh and self-test
- [x] update checklist/docs so the slice is resumable
- [x] add `json-group-count` benchmark support with dataset families and `--group-field` benchmark wiring
- [x] extend project-level and repo-level tests for programmatic and CLI benchmark coverage
- [x] update README usage, features, and future-improvement notes
- [x] run targeted tests and at least 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider benchmark report annotations that call out likely hot keys for each built-in family in a future run

## Benchmark hotspot notes slice (2026-04-16 08:31 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short benchmark-narrative refresh and self-test by mapping each built-in family to its dominant synthetic hot keys before coding
- [x] update checklist/docs so the slice is resumable
- [x] add dataset-specific benchmark notes to JSON, Markdown, and HTML benchmark artifacts for built-in families plus the bundled average-score plugin
- [x] extend project-level and repo-level tests for the richer benchmark report output
- [x] run targeted tests and 3 review passes
- [x] consider plugin-defined benchmark note hooks for third-party generators in a future run

## Plugin benchmark note hook slice (2026-04-16 09:21 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up is already explicitly scoped in the local README/checklist
- [x] do a short Python callable-signature refresh and self-test for optional plugin benchmark note hooks
- [x] update checklist/docs so the slice is resumable
- [x] add a plugin-defined benchmark note hook so third-party generators can describe hotspot narratives without touching the core runner
- [x] surface the new note hook in plugin inspection/catalog metadata and docs
- [x] extend project-level and repo-level tests for the richer plugin benchmark note flow
- [x] run targeted tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Plugin docs pages slice (2026-04-16 21:00 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the next follow-up was already explicitly scoped in the local README/checklist
- [x] do a short Python `os.path.relpath` / slugged-filename refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add dedicated per-plugin Markdown/HTML docs pages from the `catalog-plugins` flow
- [x] link catalog quick-link landing cards to the dedicated docs pages when `--docs-dir` is provided
- [x] extend project-level and repo-level tests for generated plugin docs pages and catalog links
- [x] run targeted tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider release-to-release comparison pages or richer docs-site navigation for larger plugin sets in a future run

## Structured benchmark annotations slice (2026-04-17 11:21 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the previous wrap-up already scoped this follow-up clearly
- [x] do a short Python JSON-shape/renderer refresh and self-test for annotation objects before coding
- [x] update checklist/docs so the slice is resumable
- [x] let benchmark notes carry structured annotation objects alongside plain strings
- [x] render structured annotations in benchmark JSON, Markdown, and HTML artifacts
- [x] update the bundled average-score plugin to emit interview-ready structured hotspot annotations
- [x] normalize plugin benchmark paths to repo-relative values so committed artifacts stay portable
- [x] extend project-level and repo-level tests for annotation payloads and repo-relative plugin paths
- [x] generate a committed example benchmark artifact set that showcases the new structured annotations
- [x] run targeted tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider optional benchmark-annotation filters or collapse modes when one plugin emits many reviewer callouts in a future run

## Batch annotation preset slice (2026-04-17 18:13 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the previous wrap-up already scoped the preset follow-up clearly
- [x] do a short Python dataclass/relative-path refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add batch benchmark preset export support that emits both full and filtered annotation views in one run
- [x] keep timing/heatmap artifacts shared across preset views so side-by-side comparisons stay stable
- [x] extend project-level and repo-level tests for manifest output and preset artifact generation
- [x] generate committed example preset-batch artifacts for the project-week plugin benchmark
- [x] run targeted tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider a lightweight landing page that links plugin catalogs, plugin doc pages, benchmark reports, and annotation-batch manifests into one portfolio-friendly docs index

## Docs index slice (2026-04-17 19:06 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the previous wrap-up already scoped the docs-index follow-up clearly
- [x] do a short Python `Path` / relative-link refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add a `docs-index` landing-page flow that links plugin catalogs, plugin docs, inspection diffs, benchmark reports, and annotation-batch manifests
- [x] generate committed Mini MapReduce docs artifacts for the plugin catalog, per-plugin pages, diff bundle, project-week benchmark bundle, and docs index
- [x] extend project-level and repo-level tests for real docs-index discovery and CLI output
- [x] run targeted tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider richer plugin examples beyond score aggregation, such as sessionization or log-latency summaries

## Service-latency plugin slice (2026-04-17 19:14 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the previous wrap-up already scoped the richer-plugin follow-up clearly
- [x] do a short Python percentile/latency-summary refresh and nearest-rank self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add a bundled `plugins_service_latency.py` example that emits structured latency summaries (`count`, `avg_ms`, `p95_ms`, `max_ms`)
- [x] give the new plugin deterministic benchmark families plus structured incident/batch hotspot annotations
- [x] extend project-level and repo-level tests for structured latency output, benchmark metadata, and catalog discovery
- [x] regenerate the committed Mini MapReduce artifact bundle so the catalog, plugin pages, diff report, and docs index include the new service-latency plugin
- [x] run targeted tests and 3 review passes (link audit, publishability audit, and commit-pinned/source-path review fixed the absolute-path leak in inspection artifacts before publish)
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider a follow-up plugin example such as sessionization or streaming-window summaries


## Sessionization plugin slice (2026-04-17 19:43 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] do brief web research on session-window/session-gap semantics to keep the plugin story grounded in real stream-processing terminology
- [x] do a short Python `datetime` / session-gap self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add a bundled `plugins_sessionization.py` example that summarizes per-user sessions from `user,timestamp,page` event streams
- [x] give the new plugin deterministic benchmark families plus structured launch-day/exam-week hotspot annotations
- [x] extend project-level and repo-level tests for session summary output, benchmark metadata, and catalog discovery
- [x] regenerate the committed Mini MapReduce artifact bundle so the catalog, plugin pages, diff report, sessionization benchmark report, and docs index include the new plugin
- [x] run targeted tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider a follow-up plugin example such as streaming-window summaries or rolling aggregations

## Watermark late-summary plugin slice (2026-04-17 21:01 UTC run)
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] do brief web research on event-time watermarks / allowed lateness semantics to keep the plugin story grounded in real streaming terminology
- [x] do a short Python `datetime` / event-time self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add a bundled `plugins_watermark_late_summary.py` example that summarizes accepted late events, dropped late events, and hottest replay windows from `stream,event_time,arrival_time,value` rows
- [x] give the new plugin deterministic benchmark families plus structured replay/backfill hotspot annotations
- [x] extend project-level and repo-level tests for watermark summary output, benchmark metadata, and catalog discovery
- [x] regenerate the committed Mini MapReduce artifact bundle so the catalog, plugin pages, diff report, sensor-backfill benchmark report, and docs index include the new plugin
- [x] run targeted tests and 3 review passes
- [ ] run secret scan before push
- [ ] commit, push, and add wrap-up
- [ ] consider a follow-up plugin example such as rolling-window joins or release-to-release comparison pages

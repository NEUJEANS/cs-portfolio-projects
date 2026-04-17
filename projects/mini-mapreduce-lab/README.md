# mini-mapreduce-lab

A compact Python project that demonstrates the map → combine → partition → reduce pipeline on local text and JSONL data.

## Why it is interesting
- shows the core execution model behind Hadoop-style batch processing without heavy infrastructure
- demonstrates shard partitioning, local combiners, deterministic reducer routing, and deterministic reduction
- stays practical with built-in jobs you can run on portfolio-friendly sample datasets
- now supports external Python mapper/reducer plugins so you can demo domain-specific jobs without rewriting the runner

## Features
- line-sharded execution over one or more input files
- built-in `wordcount` job for text analytics
- built-in `json-group-count` job for JSONL event aggregation
- plugin job loading via `importlib` from either a local Python file or an importable module/package path
- stable SHA-256-based partitioner to simulate multiple reducer buckets reproducibly across processes
- reducer distribution stats so you can talk about key skew in interviews
- synthetic `benchmark` mode for balanced vs skewed workloads across multiple reducer counts for built-in wordcount, built-in JSONL aggregation, or plugin jobs
- built-in JSON benchmark dataset families for generic events, incident workflows, and deployment pipelines
- benchmark JSON/Markdown/HTML artifacts now include dataset-specific hotspot notes so reviewers can connect skewed cells back to the synthetic workload design
- plugin note hooks can now emit structured benchmark annotations with severity, hotspot keys, and interview-ready takeaways in addition to plain note strings
- machine-readable JSON output with shard and record statistics
- optional CSV benchmark export for charting reducer-count comparisons in spreadsheets or notebooks
- optional shard-to-reducer heatmap CSV export for slide-ready skew visualizations
- optional Markdown benchmark report export with timing tables and shard/reducer load summaries
- optional standalone HTML benchmark report export with colorized shard/reducer heatmap tables and inline SVG charts for portfolio screenshots
- JSON-safe plugin outputs so custom jobs can emit floats or small structured values during reduction
- optional plugin-defined synthetic benchmark generators for domain-specific benchmark fixtures
- dataset-family selection so benchmarks can simulate different plugin or wordcount workload shapes without changing the runner
- plugin-advertised dataset-family metadata surfaced automatically in benchmark JSON/Markdown/HTML artifacts
- plugin inspection command for surfacing exported hooks, concise plugin summaries, and dataset-family support before running benchmarks
- optional CSV export for plugin inspection snapshots so metadata can land in docs/spreadsheets without a JSON-only step
- benchmark CSV summaries now carry plugin inspection metadata so spreadsheet artifacts stay self-describing without a separate JSON lookup
- optional adjacent plugin metadata diffs for batched inspection runs so contract changes are reviewable without hand-comparing JSON snapshots
- optional Markdown and HTML inspection reports with hook signatures, file anchors, branch-aware GitHub links, commit-pinned GitHub links, and source excerpts so plugin contract comparisons can be published as portfolio-ready artifacts
- plugin catalog command that auto-discovers bundled plugins and emits JSON/Markdown/HTML portfolio index artifacts with quick-link landing cards and review-friendly badge summaries, without repeating `--plugin` flags manually
- optional dedicated per-plugin Markdown/HTML docs pages from the catalog flow so each bundled plugin can ship as its own review-friendly portfolio page
- repo-relative plugin references in run/benchmark outputs so committed JSON/CSV/Markdown/HTML artifacts stay portable across machines

## Usage

Word count over text files:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py run \
  wordcount sample_a.txt sample_b.txt \
  --shard-size 50
```

Count JSONL records by a field:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py run \
  json-group-count events.jsonl \
  --group-field status \
  --shard-size 100
```

Simulate multiple reducers and inspect skew:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py run \
  wordcount sample.txt \
  --shard-size 50 \
  --reducers 4
```

Run a file-based plugin job that keeps the maximum score per user:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py run \
  plugin scores.csv \
  --plugin projects/mini-mapreduce-lab/plugins_top_score.py \
  --reducers 2
```

Run a module-based plugin from an importable package on `PYTHONPATH`:

```bash
PYTHONPATH=. python3 projects/mini-mapreduce-lab/mapreduce.py run \
  plugin scores.csv \
  --plugin demo_plugins.topscore \
  --reducers 2
```

Benchmark balanced vs skewed synthetic inputs for the built-in wordcount job:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --job wordcount \
  --scenario skewed \
  --records 5000 \
  --shard-size 250 \
  --reducers 1 2 4 8
```

Benchmark the built-in JSONL grouping job on incident-style status streams:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --job json-group-count \
  --group-field status \
  --scenario skewed \
  --dataset-family incidents \
  --records 5000 \
  --shard-size 250 \
  --reducers 1 2 4 8
```

Write the benchmark result to disk:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --scenario balanced \
  --reducers 1 4 8 \
  --output benchmark.json
```

Write both JSON and CSV benchmark outputs for charts or slide-ready tables:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --scenario skewed \
  --records 10000 \
  --reducers 1 2 4 8 \
  --output benchmark.json \
  --csv-output benchmark.csv
```

Write an additional shard-to-reducer heatmap CSV you can turn into a spreadsheet heatmap:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --scenario skewed \
  --records 10000 \
  --shard-size 250 \
  --reducers 2 4 8 \
  --output benchmark.json \
  --csv-output benchmark.csv \
  --heatmap-output benchmark-heatmap.csv
```

Write a Markdown report artifact that can drop straight into a portfolio repo, issue comment, or blog draft:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --scenario skewed \
  --records 10000 \
  --shard-size 250 \
  --reducers 2 4 8 \
  --output benchmark.json \
  --csv-output benchmark.csv \
  --heatmap-output benchmark-heatmap.csv \
  --report-output benchmark-report.md
```

Write a standalone HTML report artifact you can open locally or publish with the repo's docs. The page now includes inline SVG timing and reducer-load charts in addition to the heatmap table:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --scenario skewed \
  --records 10000 \
  --shard-size 250 \
  --reducers 2 4 8 \
  --output benchmark.json \
  --csv-output benchmark.csv \
  --heatmap-output benchmark-heatmap.csv \
  --report-output benchmark-report.md \
  --html-output benchmark-report.html
```

Benchmark a plugin job on deterministic synthetic score data so the same artifact pipeline works for custom reducers too:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --job plugin \
  --plugin projects/mini-mapreduce-lab/plugins_top_score.py \
  --scenario skewed \
  --records 5000 \
  --shard-size 250 \
  --reducers 2 4 8 \
  --output plugin-benchmark.json \
  --csv-output plugin-benchmark.csv \
  --heatmap-output plugin-benchmark-heatmap.csv \
  --report-output plugin-benchmark-report.md \
  --html-output plugin-benchmark-report.html
```

Inspect a plugin before running it so portfolio reviewers can see which hooks, call signatures, concise hook doc summaries, source line numbers, file anchors, branch-aware GitHub blob links, commit-pinned GitHub blob links, source excerpts, and benchmark families it exports:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py inspect-plugin \
  --plugin projects/mini-mapreduce-lab/plugins_average_score.py
```

Write both JSON and CSV inspection artifacts when you want a one-row metadata snapshot for docs or spreadsheets:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py inspect-plugin \
  --plugin projects/mini-mapreduce-lab/plugins_average_score.py \
  --output plugin-inspection.json \
  --csv-output plugin-inspection.csv
```

Repeat `--plugin` to batch multiple plugins into one JSON/CSV artifact when you want a side-by-side portfolio comparison of supported hooks and dataset families:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py inspect-plugin \
  --plugin projects/mini-mapreduce-lab/plugins_average_score.py \
  --plugin projects/mini-mapreduce-lab/plugins_top_score.py \
  --output plugin-batch.json \
  --csv-output plugin-batch.csv
```

Add `--diff` to the same batched inspection flow when you want the JSON payload to include field-by-field contract changes between adjacent plugins in the order provided:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py inspect-plugin \
  --plugin projects/mini-mapreduce-lab/plugins_average_score.py \
  --plugin projects/mini-mapreduce-lab/plugins_top_score.py \
  --diff \
  --output plugin-diff.json
```

Write publishable Markdown and HTML inspection artifacts from the same diff-aware batch so plugin contract changes, file anchors, branch-aware GitHub links, commit-pinned GitHub links, and source excerpts can land directly in docs or GitHub Pages:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py inspect-plugin \
  --plugin projects/mini-mapreduce-lab/plugins_average_score.py \
  --plugin projects/mini-mapreduce-lab/plugins_top_score.py \
  --diff \
  --report-output plugin-diff-report.md \
  --html-output plugin-diff-report.html
```

Auto-discover every bundled plugin under the project directory and generate a portfolio-ready catalog plus adjacent diffs in one step. The Markdown/HTML catalog now starts with quick-link landing cards that summarize hook coverage, dataset families, and source-link readiness for each plugin:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py catalog-plugins \
  --root projects/mini-mapreduce-lab \
  --diff \
  --output plugin-catalog.json \
  --report-output plugin-catalog.md \
  --html-output plugin-catalog.html
```

Add `--docs-dir` when you want the same catalog run to generate dedicated per-plugin Markdown and HTML docs pages that link back to the shared catalog index:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py catalog-plugins \
  --root projects/mini-mapreduce-lab \
  --report-output plugin-catalog.md \
  --html-output plugin-catalog.html \
  --docs-dir docs/plugin-pages
```

Switch benchmark dataset families to model different workload shapes. For example, the built-in `json-group-count` benchmark now supports `default`, `incidents`, and `deployments` families, while the average-score plugin exposes `default`, `exam-cram`, and `project-week` families:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --job plugin \
  --plugin projects/mini-mapreduce-lab/plugins_average_score.py \
  --scenario balanced \
  --dataset-family project-week \
  --records 240 \
  --shard-size 30 \
  --reducers 2 4 \
  --output project-week-benchmark.json
```

## Plugin contract

A plugin is a Python file with:

- `JOB_NAME = "human-readable-name"` (optional)
- `map_records(lines)` → yields `(key, value)` pairs
- `combine_values(key, values)` → optional shard-local combiner for non-sum jobs
- `reduce_key(key, values)` → returns a JSON-serializable result for that key
- `benchmark_records(scenario, records, seed)` → optional synthetic input generator for plugin benchmarks
- `benchmark_records(scenario, records, seed, dataset_family)` → optional extended form when a plugin wants multiple workload families
- `benchmark_notes(scenario)` / `benchmark_notes(scenario, dataset_family)` / `benchmark_notes(scenario, dataset_family, records, seed)` → optional benchmark hotspot narrative hook whose returned list can contain plain strings or JSON-safe annotation dicts with fields like `title`, `detail`, `severity`, `hotspot_keys`, and `takeaway`; both forms are surfaced in benchmark JSON/Markdown/HTML artifacts

Pass `--plugin` either as a filesystem path like `projects/mini-mapreduce-lab/plugins_top_score.py` or as a dotted module path like `demo_plugins.topscore` when the package is importable on `PYTHONPATH`.

The included `plugins_top_score.py` example parses `name,score` lines and keeps the maximum score for each user. It uses both `combine_values` and `reduce_key` so the shard-local combiner does not accidentally turn a max-style reduction back into summation.

The new `plugins_average_score.py` example shows a richer pattern: the mapper emits `{"sum": ..., "count": ...}` objects, the combiner merges those objects per shard, the reducer returns a float average, the optional `benchmark_records()` hook emits domain-shaped synthetic score streams for deterministic plugin benchmarks, and the optional `benchmark_notes()` hook explains which synthetic cohort should become the hotspot in each family. It now supports named dataset families such as `exam-cram` and `project-week`, advertises them via `BENCHMARK_DATASET_FAMILIES`, and exposes both the generator and note hook through `inspect-plugin` / `catalog-plugins` metadata so benchmark artifacts can surface the supported families automatically. That makes the project easier to discuss as a stepping stone from simple counting jobs toward typed aggregations and analytics pipelines.

## Output shape

`run` mode still emits a compact per-job JSON payload:

```json
{
  "job": "plugin-max-score",
  "plugin": "projects/mini-mapreduce-lab/plugins_top_score.py",
  "reducers": 2,
  "reducer_stats": [
    {
      "records": 1,
      "reducer": 0,
      "unique_keys": 1
    }
  ],
  "output": {
    "alice": 11,
    "bob": 8
  }
}
```

`benchmark` mode now also includes benchmark `job`/`plugin` metadata, `dataset_family`, optional `available_dataset_families`, dataset-specific `benchmark_notes`, richer `benchmark_note_annotations`, and `plugin_benchmark_note_hook`, plus `heatmap_rows`, where each row captures one shard/reducer cell. `inspect-plugin` / `catalog-plugins` artifacts likewise surface the optional benchmark note hook alongside the mapper/reducer/combiner/generator metadata. `--report-output` can turn the same data into a narrative Markdown artifact, and `--html-output` can render a standalone colorized report page for screenshots or GitHub Pages publishing:

```json
{
  "available_dataset_families": ["default", "exam-cram", "project-week"],
  "dataset_family": "project-week",
  "heatmap_rows": [
    {
      "scenario": "skewed",
      "seed": 42,
      "reducers": 4,
      "shard_index": 0,
      "reducer": 2,
      "records": 187,
      "unique_keys": 3
    }
  ]
}
```

## Test

```bash
python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py
python3 -m unittest tests/test_mini_mapreduce.py
```

## Interview talking points
- why combiners reduce shuffle volume before the global reduce step
- how partitioning affects reducer balance and hot-key skew
- how deterministic benchmark fixtures make systems demos reproducible
- why plugin-based jobs make a systems lab look extensible instead of hard-coded
- why timing alone can mislead without reducer-distribution metrics beside it
- how shard-to-reducer heatmaps make hot-key skew visible in demos, write-ups, and interviews
- how generated Markdown reports make benchmark evidence easier to reuse in READMEs, blogs, and portfolio case studies
- how standalone HTML artifacts with inline SVG charts make systems benchmarks easier to present visually without a notebook stack

## Future improvements
- add repository-level inspection summaries or release-to-release comparison pages that compare multiple plugin snapshots across releases, not just adjacent runs
- add optional benchmark-annotation filters or collapse modes when a plugin emits many reviewer callouts in one report

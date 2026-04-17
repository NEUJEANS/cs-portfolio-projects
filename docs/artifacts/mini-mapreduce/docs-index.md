# Mini MapReduce docs index

A lightweight landing page for the committed Mini MapReduce artifacts so reviewers can jump from the top-level project README into plugin catalogs, dedicated plugin docs, inspection diffs, benchmark reports, and annotation-batch presets without hunting through the repo tree.

## Browser-first links

- [Plugin catalog HTML](plugin-catalog.html)
- [Inspection diff HTML — Plugin Comparison](plugin-comparison-diff.html)
- [Benchmark report HTML — 2026-04-17 · Annotation View](2026-04-17-annotation-view-report.html)
- [Benchmark report HTML — 2026-04-17 · Incident Spike Latency](2026-04-17-incident-spike-latency-report.html)
- [Benchmark report HTML — 2026-04-17 · Project Week](2026-04-17-project-week-report.html)
- [Benchmark report HTML — 2026-04-17 · Structured Annotations](2026-04-17-structured-annotations-report.html)
- [Annotation batch HTML — 2026-04-17 · Annotation Batch / full](2026-04-17-annotation-batch-full.html)
- [Annotation batch HTML — 2026-04-17 · Annotation Batch / portfolio-tight](2026-04-17-annotation-batch-portfolio-tight.html)

## Plugin catalog

- [Markdown](plugin-catalog.md) · [HTML](plugin-catalog.html) · [JSON](plugin-catalog.json) · [CSV](plugin-catalog.csv)

## Plugin pages

| Plugin page | Description | Links |
| --- | --- | --- |
| `plugin-average-score` | Dedicated plugin reference page with hook summaries and source excerpts. | [Markdown](plugin-pages/plugin-average-score.md) · [HTML](plugin-pages/plugin-average-score.html) |
| `plugin-max-score` | Dedicated plugin reference page with hook summaries and source excerpts. | [Markdown](plugin-pages/plugin-max-score.md) · [HTML](plugin-pages/plugin-max-score.html) |
| `plugin-service-latency` | Dedicated plugin reference page with hook summaries and source excerpts. | [Markdown](plugin-pages/plugin-service-latency.md) · [HTML](plugin-pages/plugin-service-latency.html) |

## Inspection diffs

| Diff bundle | Description | Links |
| --- | --- | --- |
| Plugin Comparison | Adjacent plugin contract comparison bundle with publishable Markdown/HTML plus machine-readable JSON. | [Markdown](plugin-comparison-diff.md) · [HTML](plugin-comparison-diff.html) · [JSON](plugin-comparison-diff.json) |

## Benchmark reports

| Report bundle | Description | Links |
| --- | --- | --- |
| 2026-04-17 · Annotation View | Benchmark report bundle with browser-friendly HTML plus raw JSON/CSV companions. | [Markdown](2026-04-17-annotation-view-report.md) · [HTML](2026-04-17-annotation-view-report.html) · [JSON](2026-04-17-annotation-view-benchmark.json) · [CSV](2026-04-17-annotation-view-benchmark.csv) · [Heatmap CSV](2026-04-17-annotation-view-heatmap.csv) |
| 2026-04-17 · Incident Spike Latency | Benchmark report bundle with browser-friendly HTML plus raw JSON/CSV companions. | [Markdown](2026-04-17-incident-spike-latency-report.md) · [HTML](2026-04-17-incident-spike-latency-report.html) · [JSON](2026-04-17-incident-spike-latency-benchmark.json) · [CSV](2026-04-17-incident-spike-latency-benchmark.csv) · [Heatmap CSV](2026-04-17-incident-spike-latency-heatmap.csv) |
| 2026-04-17 · Project Week | Benchmark report bundle with browser-friendly HTML plus raw JSON/CSV companions. | [Markdown](2026-04-17-project-week-report.md) · [HTML](2026-04-17-project-week-report.html) · [JSON](2026-04-17-project-week-benchmark.json) · [CSV](2026-04-17-project-week-benchmark.csv) · [Heatmap CSV](2026-04-17-project-week-heatmap.csv) |
| 2026-04-17 · Structured Annotations | Benchmark report bundle with browser-friendly HTML plus raw JSON/CSV companions. | [Markdown](2026-04-17-structured-annotations-report.md) · [HTML](2026-04-17-structured-annotations-report.html) · [JSON](2026-04-17-structured-annotations-benchmark.json) · [CSV](2026-04-17-structured-annotations-benchmark.csv) · [Heatmap CSV](2026-04-17-structured-annotations-heatmap.csv) |

## Annotation batch manifests

### 2026-04-17 · Annotation Batch

- Manifest: [JSON](2026-04-17-annotation-batch-manifest.json)
- Shared artifacts: [Shared CSV](2026-04-17-annotation-batch-shared.csv) · [Shared heatmap CSV](2026-04-17-annotation-batch-shared-heatmap.csv)

| Preset | Filter summary | Links |
| --- | --- | --- |
| `full` | Full annotation view with every structured reviewer callout rendered. | [Markdown](2026-04-17-annotation-batch-full.md) · [HTML](2026-04-17-annotation-batch-full.html) · [JSON](2026-04-17-annotation-batch-full.json) |
| `portfolio-tight` | Filtered annotation view for portfolio screenshots: keep risk/watch callouts, show one card, and collapse the rest into a summary. <br>severity=risk, watch<br>limit=1<br>overflow=summary | [Markdown](2026-04-17-annotation-batch-portfolio-tight.md) · [HTML](2026-04-17-annotation-batch-portfolio-tight.html) · [JSON](2026-04-17-annotation-batch-portfolio-tight.json) |

## Suggested portfolio usage

- Lead with the HTML report links when you want a browser-friendly walkthrough instead of raw terminal output.
- Use the plugin catalog first when someone wants to understand the extensibility story before reading the benchmark results.
- Use the inspection diff bundle when you want to compare how two plugins expose different hook contracts or dataset families.
- Use the annotation-batch manifest when you want both the full and portfolio-tight reviewer narratives from one shared benchmark run.
- Link this index from the project README so future slices stay discoverable as more artifact families are added.

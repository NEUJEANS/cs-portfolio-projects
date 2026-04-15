# Mini MapReduce HTML report refresh

## Goal
Add a portfolio-friendly HTML artifact for benchmark runs without introducing third-party templating or plotting dependencies.

## Refresher
- `html.escape(value, quote=True)` is enough for safe interpolation of benchmark labels and numeric metadata in a static report.
- Inline table-cell backgrounds via `rgba(...)` are a simple way to create a deterministic heatmap without JavaScript.
- Reusing the existing benchmark summary data keeps Markdown and HTML outputs aligned, which lowers maintenance risk.

## Self-test before coding
- Build the timing table from the existing `timings_ms` rows instead of recomputing metrics.
- Reuse `heatmap_rows` grouped by reducer count so the HTML report matches the Markdown report's hottest/coldest-cell narrative.
- Keep the output fully standalone: one HTML file, inline CSS, no external assets.

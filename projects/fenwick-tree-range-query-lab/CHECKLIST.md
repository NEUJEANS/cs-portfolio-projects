# Fenwick Tree Range Query Lab Checklist

## Vertical slice: benchmark comparison pack
- [x] identify a meaningful gap in the project story, the missing comparison against a segment tree baseline
- [x] refresh the core complexity model for Fenwick range-add/range-sum and lazy segment tree range-add/range-sum
- [x] add a deterministic benchmark workload generator for mixed queries and updates
- [x] implement a lazy segment tree baseline for the same workload
- [x] export benchmark results as JSON, CSV, and Markdown
- [x] expand tests for mixed-operation correctness and benchmark CLI coverage
- [x] generate committed sample benchmark artifacts for the README
- [x] document the new workflow in the project README

## Vertical slice: screenshot-friendly benchmark SVG export
- [x] confirm the next weak spot is visual benchmark storytelling after the JSON/CSV/Markdown artifact pack
- [x] refresh lightweight SVG layout rules for stable viewBox sizing and text anchoring
- [x] add a standalone SVG renderer for throughput and per-operation latency comparison
- [x] wire `benchmark --svg-output` into the CLI and committed artifact workflow
- [x] expand tests to cover the SVG renderer and CLI export path
- [x] regenerate the committed sample benchmark artifacts, including the SVG chart
- [x] document the chart export workflow in the project README

## Vertical slice: benchmark workload presets
- [x] confirm the next weak spot is preset coverage beyond one balanced workload
- [x] refresh how query-heavy, update-heavy, and point-set-heavy mixes should differ
- [x] add named benchmark presets with optional ratio overrides
- [x] thread preset metadata through benchmark JSON, CSV, Markdown, and SVG outputs
- [x] expand tests for preset resolution and CLI preset usage
- [x] generate committed preset artifacts for query-heavy, update-heavy, and point-set-heavy runs
- [x] document preset-driven benchmark workflows in the project README

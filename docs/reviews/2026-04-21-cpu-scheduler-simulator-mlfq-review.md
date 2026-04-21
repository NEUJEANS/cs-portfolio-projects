# CPU scheduler MLFQ review log

## Pass 1, metadata scoping audit
- Issue found: compare and benchmark reports showed MLFQ run metadata even when the selected algorithm set did not include MLFQ, which made narrowed comparisons look misleading.
- Fix: add `comparison_includes_mlfq()` and `benchmark_includes_mlfq()` helpers, then emit MLFQ metadata in Markdown, HTML, and SVG only when MLFQ is actually present.

## Pass 2, standalone result reproducibility audit
- Issue found: a direct `mlfq` run produced correct scheduling metrics, but the result payload itself did not preserve the active MLFQ settings, so downstream JSON/report consumers could lose the queue ladder and boost interval.
- Fix: store algorithm-specific settings in `simulate()` results and let `format_report()` fall back to those persisted values.

## Pass 3, documentation and smoke-flow audit
- Issue found: the README still described MLFQ as future work and did not show the new CLI flags in the main usage examples, which weakened the portfolio story.
- Fix: refresh the README feature list, quick-start commands, example output, compare/benchmark artifact commands, and next-extension list, then rerun compare/benchmark smoke generation.

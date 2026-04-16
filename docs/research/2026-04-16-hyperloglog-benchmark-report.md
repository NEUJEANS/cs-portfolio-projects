# HyperLogLog benchmark/report research

## Goal
Add a follow-up slice to `hyperloglog-cardinality-lab` that demonstrates the practical precision-vs-error-vs-memory tradeoff with reproducible benchmark artifacts a student can show in a portfolio.

## Brief findings
- Redis positions HyperLogLog as a constant-memory approximate distinct counter and highlights mergeability (`PFMERGE`) as the practical distributed-systems story; that supports adding a benchmark/report mode focused on storage/accuracy tradeoffs rather than just one-off estimates.
- Apache DataSketches documentation frames HLL evaluation around compactness, speed, and error behavior across sketch sizes, which maps well to a sweep over multiple precisions (`p`) and target cardinalities.
- For a teaching/portfolio CLI, a dense-register byte estimate is a simple memory proxy that keeps comparisons understandable without pretending this Python JSON representation is production-optimized.
- A Markdown report generated directly by the CLI is useful because it becomes a publishable artifact for GitHub Pages, screenshots, or README embeds.
- Deterministic synthetic trials matter: if the same seed reproduces the same sweep, students can discuss results confidently and regenerate artifacts during interviews.

## Applied product decisions
- add a `benchmark` subcommand instead of overloading `simulate`
- accept comma-separated precision and cardinality lists so one command can generate a meaningful comparison table
- produce both JSON and Markdown outputs so the raw data and a human-facing summary stay in sync
- report dense register bytes plus theoretical error bound alongside observed mean/max relative error
- generate a committed example benchmark report artifact for the repo

## References
- Redis HyperLogLog docs: constant-memory distinct counting, approximate error, and merge-oriented usage
- Apache DataSketches HLL overview: storage/accuracy framing across sketch sizes and union-oriented workflows

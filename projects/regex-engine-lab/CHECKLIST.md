# regex-engine-lab checklist

## Current slice (2026-04-19 19:51 UTC run)
- [x] confirm `main` still matches `origin/main` before editing and resume the already-dirty `regex-engine-lab` explainer slice instead of switching projects midstream
- [x] skip external web research because this slice is a repo-local portfolio storytelling follow-up rather than a new regex-theory feature
- [x] do a short Python/AST-summary refresh and self-test for turning `explain()` payloads into concise showcase cards
- [x] update the checklist so this explainer slice stays resumable on later cron runs
- [x] add tiny AST/NFA explainer cards beside the trace + benchmark showcase page using the existing `explain()` output
- [x] summarize each showcase trace pattern into AST story/shape + NFA shape metrics without introducing a frontend build step
- [x] regenerate and commit `docs/artifacts/regex-engine-lab/showcase.html`
- [x] update README usage/examples plus research/learning/review notes for the explainer flow
- [x] extend regression coverage for explainer counts, AST stories, and showcase HTML wording
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan
- [x] commit, push, and write the wrap-up

## Completed slices
- [x] initial Thompson-NFA regex engine with fullmatch/search/explain CLI flows
- [x] shorthand escape classes (`\d`, `\w`, `\s`, and inverses) using the project’s ASCII teaching subset
- [x] JSON trace output for step-by-step NFA execution in fullmatch and search modes
- [x] benchmark comparisons against Python `re` for single-case and built-in sample-suite runs
- [x] JSON-backed benchmark suites with committed workload files and artifact exports
- [x] suite-level tags and repeatable include/exclude filters for interview-demo vs portfolio-batch benchmark subsets
- [x] browser-friendly HTML benchmark dashboards for sample, portfolio, and interview-demo benchmark suites
- [x] combined showcase page that ties the trace walkthroughs to the benchmark dashboards
- [x] tiny AST/NFA explainer cards embedded in the combined showcase page

## Current quality checks
- [x] README documents fullmatch/search/trace/benchmark usage plus suite-file, tag-filter, and HTML-dashboard flows
- [x] tests cover parser behavior, shorthand classes, traces, benchmark agreement, suite loading, tag validation, HTML rendering, and CLI error handling
- [x] project is resumable through committed workload JSON, benchmark artifacts, checklist/research/learning notes, review logs, and wrap-ups

## Next follow-up ideas
- [ ] add optional Unicode-aware shorthand classes as a contrast with the current ASCII teaching mode
- [ ] add a tiny benchmark-suite preset catalog if more workload families accumulate beyond the current single JSON example
- [ ] add a trace-to-explainer SVG or HTML timeline card if the portfolio needs a more visual walkthrough than raw JSON

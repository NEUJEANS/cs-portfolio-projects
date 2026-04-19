# regex-engine-lab checklist

## Current slice (2026-04-19 19:08 UTC run)
- [x] confirm `main` still matches `origin/main` before editing and keep the regex-engine momentum instead of switching projects
- [x] skip external web research because this slice only needed a repo-local renderer/report refresh rather than new algorithm evidence
- [x] do a short Python/static-HTML refresh and self-test for turning an existing benchmark payload into a browser-friendly artifact without a frontend build step
- [x] update the checklist so this HTML-dashboard slice is resumable on later cron runs
- [x] add `benchmark --html-out` and render a benchmark dashboard from the existing JSON/Markdown report payload
- [x] regenerate and commit the sample-suite, full portfolio-suite, and interview-demo HTML dashboards under `docs/artifacts/regex-engine-lab/`
- [x] update README usage/examples and sample-artifact notes so the HTML dashboard flow is discoverable
- [x] extend regression coverage for HTML rendering and CLI artifact writing
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

## Current quality checks
- [x] README documents fullmatch/search/trace/benchmark usage plus suite-file, tag-filter, and HTML-dashboard flows
- [x] tests cover parser behavior, shorthand classes, traces, benchmark agreement, suite loading, tag validation, HTML rendering, and CLI error handling
- [x] project is resumable through committed workload JSON, benchmark artifacts, checklist/research/learning notes, review logs, and wrap-ups

## Next follow-up ideas
- [ ] add optional Unicode-aware shorthand classes as a contrast with the current ASCII teaching mode
- [ ] add cross-links or a tiny combined showcase page that ties trace artifacts and benchmark dashboards together
- [ ] add a tiny benchmark-suite preset catalog if more workload families accumulate beyond the current single JSON example

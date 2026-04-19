# regex-engine-lab checklist

## Current slice (2026-04-19 19:11 UTC run)
- [x] confirm `main` still matches `origin/main` before editing and keep the regex-engine momentum instead of switching projects
- [x] skip external web research because this slice only needed a repo-local showcase/linking follow-up rather than new regex theory
- [x] do a short Python/static-HTML refresh and self-test for cross-linking committed trace + benchmark artifacts with relative paths
- [x] update the checklist so this showcase slice is resumable on later cron runs
- [x] add `showcase-demo --html-out ... --artifact-dir ...` to build a combined landing page over the committed trace JSON and benchmark dashboard artifacts
- [x] cross-link each trace card to the benchmark dashboards that exercise the same pattern/mode pair so the teaching story flows from behavior to performance
- [x] regenerate and commit `docs/artifacts/regex-engine-lab/showcase.html`
- [x] update README usage/examples, sample-artifact notes, and resumability docs for the showcase flow
- [x] extend regression coverage for showcase path resolution, related-dashboard matching, HTML rendering, and CLI writing
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

## Current quality checks
- [x] README documents fullmatch/search/trace/benchmark usage plus suite-file, tag-filter, and HTML-dashboard flows
- [x] tests cover parser behavior, shorthand classes, traces, benchmark agreement, suite loading, tag validation, HTML rendering, and CLI error handling
- [x] project is resumable through committed workload JSON, benchmark artifacts, checklist/research/learning notes, review logs, and wrap-ups

## Next follow-up ideas
- [ ] add optional Unicode-aware shorthand classes as a contrast with the current ASCII teaching mode
- [ ] add a tiny AST/NFA explainer card that sits beside the trace and benchmark showcase page
- [ ] add a tiny benchmark-suite preset catalog if more workload families accumulate beyond the current single JSON example

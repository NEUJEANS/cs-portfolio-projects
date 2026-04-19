# regex-engine-lab checklist

## Current slice (2026-04-19 18:51 UTC run)
- [x] confirm `main` still matches `origin/main` before editing and keep the in-progress local regex benchmark diff instead of switching projects
- [x] skip external web research because this slice only needed a brief repo-local contract refresh around benchmark-suite metadata and CLI filtering
- [x] do a short Python/CLI refresh and self-test for repeatable `argparse` tag filters plus JSON-backed suite metadata
- [x] add checklist coverage so the regex-engine project is resumable like the stronger labs in this repo
- [x] finish suite-level benchmark tags plus repeatable `--include-tag` / `--exclude-tag` filters for built-in and JSON-backed suites
- [x] regenerate and commit the sample-suite, full portfolio-suite, and interview-demo benchmark artifacts under `docs/artifacts/regex-engine-lab/`
- [x] update README usage/examples and the committed suite JSON so one workload file can drive both small interview demos and broader portfolio runs
- [x] extend regression coverage for tag parsing, normalization, filter validation, and filtered CLI outputs
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

## Current quality checks
- [x] README documents fullmatch/search/trace/benchmark usage plus the suite-file and tag-filter flows
- [x] tests cover parser behavior, shorthand classes, traces, benchmark agreement, suite loading, tag validation, and CLI error handling
- [x] project is resumable through committed workload JSON, benchmark artifacts, checklist/research/learning notes, review logs, and wrap-ups

## Next follow-up ideas
- [ ] render benchmark suites into a small HTML summary card or comparison dashboard
- [ ] add optional Unicode-aware shorthand classes as a contrast with the current ASCII teaching mode
- [ ] add a tiny benchmark-suite preset catalog if more workload families accumulate beyond the current single JSON example

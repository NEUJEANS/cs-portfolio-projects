# regex-engine-lab checklist

- [x] choose a new project that adds language-runtime and automata depth to the portfolio
- [x] capture compact research notes for a regex engine vertical slice
- [x] do a short parser/NFA refresh and self-test
- [x] implement parser + Thompson-style NFA compiler + CLI
- [x] add README and usage examples
- [x] add automated tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 shorthand escape class slice
- [x] inspect the regex engine lab and choose shorthand escape classes as the next portfolio-friendly upgrade
- [x] capture a compact research note on `\d` / `\w` / `\s` semantics and scope this lab to explicit ASCII teaching behavior
- [x] do a short parser/compiler refresh and self-test for escaped token handling inside and outside bracket classes
- [x] add a resumable slice checklist file for this upgrade
- [x] implement shorthand escape classes `\d`, `\D`, `\w`, `\W`, `\s`, and `\S` in the parser, AST, compiler, and matcher
- [x] support shorthand terms inside bracket classes and document the resulting syntax in the README
- [x] add regression coverage for positive/negative shorthand classes, bracket mixing, explain output, and CLI behavior
- [x] run tests and smoke commands
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 NFA trace slice
- [x] inspect the current regex engine lab and choose step-by-step NFA state tracing as the next portfolio-friendly upgrade
- [x] capture a brief research note on why Thompson-style active-state tracing is a strong teaching and debugging surface
- [x] do a short runtime refresh and self-test for epsilon closure, per-character transitions, and leftmost search attempts
- [x] add a resumable slice checklist file for this upgrade
- [x] implement JSON trace helpers for both `fullmatch` and `search`
- [x] expose the trace flow through a new CLI subcommand and keep explain/search/fullmatch behavior stable
- [x] add regression coverage for successful traces, early-stop traces, and leftmost-search attempt reporting
- [x] generate committed sample trace artifacts and document them in the README
- [x] run tests and smoke commands
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 benchmark slice
- [x] inspect the current regex engine lab and choose benchmark parity with Python `re` as the next portfolio-friendly upgrade
- [x] capture a brief research note on `re.fullmatch` / `re.search` parity plus `time.perf_counter()` timing
- [x] do a short benchmark refresh and self-test for compiled-pattern reuse and ASCII-safe shorthand cases
- [x] add a resumable slice checklist file for this upgrade
- [x] implement a `benchmark` CLI for custom cases plus a built-in sample suite
- [x] add Markdown / JSON benchmark report output helpers
- [x] add regression coverage for benchmark helpers, CLI behavior, and artifact writing
- [x] generate committed sample benchmark artifacts and document them in the README
- [x] run tests and smoke commands
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 JSON benchmark suite slice
- [x] inspect the current regex engine lab and choose JSON-defined benchmark suites as the next portfolio-friendly upgrade
- [x] capture a brief research note on why repo-committed workload bundles make benchmark stories more reproducible and reviewable
- [x] do a short argparse / JSON validation refresh and self-test for suite-file loading edge cases
- [x] add a resumable slice checklist entry for this upgrade
- [x] implement `benchmark --suite-file` with validation, suite metadata, and reusable case loading helpers
- [x] add a committed example suite file plus generated benchmark artifacts from that suite
- [x] add regression coverage for suite loading, CLI artifact writing, invalid suite errors, and duplicate labels
- [x] run tests and smoke commands
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 combined showcase slice
- [x] inspect the current regex engine lab and choose the combined trace+benchmark showcase as the next portfolio-friendly upgrade
- [x] capture a brief research note on why a single landing page helps the portfolio narrative more than another isolated artifact
- [x] do a short static-HTML / relative-path refresh and self-test for linking committed artifacts without a frontend build step
- [x] add a resumable slice checklist entry for this upgrade
- [x] implement `showcase-demo --html-out ... --artifact-dir ...` to build a combined landing page over the committed traces and benchmark dashboards
- [x] cross-link each trace artifact to the benchmark dashboards that exercise the same regex case
- [x] add regression coverage for showcase path resolution, related-dashboard matching, HTML rendering, and CLI writing
- [x] generate the committed showcase artifact and document it in the README
- [x] run tests and smoke commands
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

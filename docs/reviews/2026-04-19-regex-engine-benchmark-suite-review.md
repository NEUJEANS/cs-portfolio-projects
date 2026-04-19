# Regex engine benchmark-suite review log — 2026-04-19

## Pass 1 — benchmark error-handling audit
- reviewed the new `benchmark --suite-file` path against the existing CLI error contract
- issue found: benchmark mode could still surface an unhandled regex syntax exception because the benchmark branch returned before the normal `RegexSyntaxError` guard used by `fullmatch`, `search`, `explain`, and `trace`
- fix applied: wrapped benchmark report execution in `RegexSyntaxError` handling so invalid benchmark patterns now return the same JSON error shape with exit code `2`
- regression added: `test_cli_reports_invalid_benchmark_pattern_errors`

## Pass 2 — report contract / backward-compatibility audit
- reread the benchmark report payload and Markdown summary to check whether the new suite metadata stayed helpful without cluttering older one-off flows
- issue found: the first implementation stamped `suite_source` onto inline single-case benchmark runs, which added noisy metadata to a previously simple output path
- fix applied: keep `suite_source` only for built-in and file-backed suites; inline single-case benchmark runs stay concise

## Pass 3 — docs + artifact audit
- reviewed the README benchmark section, the committed JSON workload example, and the generated Markdown artifact together from a reviewer perspective
- issue found: the docs needed an explicit repo path for the example suite file plus a clear pointer to the committed workload-generated artifacts so the new feature was discoverable without reading the Python source
- fix applied: added the `--suite-file ../../docs/examples/regex-engine-benchmark-suite.json` usage example and listed the new example/artifact files in the README
- reran `py_compile`, the full regex-engine-lab unit/CLI suite, the suite-file artifact generation command, and `git diff --check`
- result: no further issues found after the earlier fixes

## Pass 4 — suite data hygiene audit
- reviewed the JSON suite contract from a maintenance perspective to make sure version-controlled workloads would stay easy to compare over time
- issue found: the loader accepted duplicate case labels, which would make the Markdown/JSON reports ambiguous when multiple rows shared the same human-facing name
- fix applied: added explicit duplicate-label validation, a regression test for repeated labels, and a README note that suite-case labels must remain unique
- reran `py_compile`, the full regex-engine-lab test suite, the suite-file artifact generation command, and `git diff --check`
- result: no further issues found after the uniqueness guard landed

# Dependency graph planner benchmark dashboard refresh — 2026-04-20

## Short refresh
- Keep the HTML path as a pure renderer over the existing benchmark result payload so Markdown/JSON/CSV/HTML do not drift.
- Relative links matter for committed static artifacts: the dashboard should stay browsable after checkout, on GitHub, and from copied artifact folders.
- A useful benchmark dashboard should tell the story in layers: quick summary cards first, then aggregate winners, then per-scenario detail tables.
- When adding a new benchmark-only flag, cover both happy-path export writing and CLI misuse on unrelated commands.

## Self-test
1. Why add HTML as a renderer instead of a new benchmark workflow?
   - The benchmark command already computes the full suite result, so a renderer keeps the logic single-sourced and easier to verify.
2. Why should dashboard artifact links be relative?
   - Relative paths keep the committed HTML portable and readable in-repo instead of hard-coding machine-specific absolute paths.
3. What regression is easy to miss when adding `--benchmark-html-out`?
   - The flag can work for `benchmark` but still be accidentally accepted on other commands unless CLI misuse coverage is added.

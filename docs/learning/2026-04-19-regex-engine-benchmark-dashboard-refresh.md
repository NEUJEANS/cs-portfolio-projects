# Regex engine benchmark dashboard refresh and self-test — 2026-04-19

## Refresh
- keep the HTML path as a pure renderer over the existing benchmark report dictionary so JSON/Markdown/HTML stay in sync
- prefer a static single-file dashboard over a JS-heavy app for this repo because the artifacts should be easy to commit, diff, and browse on GitHub Pages
- show the benchmark story at two levels: top summary cards for recruiter scanning, then case-by-case cards/tables for technical walkthroughs
- preserve the suite metadata (`suite_source`, `applied_filters`, `tags`) in the dashboard so filtered interview subsets still explain themselves without opening the raw JSON

## Self-test
1. Why add HTML as a renderer instead of a brand-new benchmark command?
   - the benchmark command already computes the full report payload, so a renderer keeps the logic single-sourced and lowers drift risk.
2. What makes the dashboard portfolio-friendly instead of just pretty?
   - it surfaces the benchmark story quickly: suite summary, agreement status, mode split, tag counts, and per-case metrics in one static page.
3. What should happen when the same benchmark suite is filtered for an interview demo?
   - the HTML should still show the original suite source plus the applied include/exclude filters so the smaller subset remains understandable and reproducible.

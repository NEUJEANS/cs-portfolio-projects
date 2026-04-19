# log-analyzer checklist

## Current slice (2026-04-19 00:01 UTC run)
- [x] resume the queued annotation-theme follow-up after confirming `main` matches `origin/main`
- [x] ship `TIMESTAMP=THEME|LABEL` support so trend-card and comparison-card annotations render deploy/rollback/incident/recovery/note markers with distinct SVG/HTML styling
- [x] fail fast on unknown theme names so mistyped CLI annotations do not silently degrade into plain notes
- [x] refresh committed annotated artifact samples plus README usage/examples to demonstrate themed markers and badges
- [x] run targeted tests, themed export smoke checks, and 3 review passes
- [x] run secret scan, commit, push, and write the wrap-up

## Completed slices
- [x] parse common and combined access-log formats
- [x] summarize status, method, IP, path, referrer, and user-agent counts
- [x] normalize request-latency values and export summary CSV output
- [x] parse Nginx `request_time=` / `upstream_response_time=` fields and export hotspot CSVs
- [x] add hotspot status/method drill-down filters with self-describing JSON/CSV metadata
- [x] add inclusive `--window-start` / `--window-end` filtering with matched/excluded counts and export metadata
- [x] add minute/hour time-bucket summaries and `--time-bucket-csv` exports for chart-ready trend analysis
- [x] add repeatable `--facet-field` support plus per-facet hotspot/time-bucket breakdowns and dedicated facet CSV exports
- [x] add standalone `--time-bucket-card-svg` / `--time-bucket-card-html` exports for slide-ready observability trend cards and browser-friendly bucket summary pages
- [x] add `--facet-compare-field` / `--facet-compare-values` release-review helpers with side-by-side JSON/text summaries and dedicated comparison CSV exports
- [x] add `--facet-compare-card-svg` / `--facet-compare-card-html` release-review artifacts plus a committed sample bundle under `docs/artifacts/log-analyzer/`
- [x] add repeatable `--card-annotation` callouts so trend cards and comparison cards can pin deploy/incident markers onto selected buckets

## Current quality checks
- [x] README reflects the shipped facet flags, side-by-side comparison helpers, hotspot/time-bucket workflows, trend-card exports, comparison-card exports, annotation controls, and export metadata
- [x] unittest coverage includes named-field parsing, facet comparison summaries/CSV exports, comparison-card rendering, annotation-aware card rendering, file exports, and CLI validation errors
- [x] project is resumable via review logs, committed artifacts, and wrap-up notes in `docs/`

## Next follow-up ideas
- [ ] optionally support facet-aware ranking summaries for top IP/path tables when richer custom log formats include deployment labels
- [ ] consider PNG export helpers or a small gallery index page that links trend cards and comparison cards together
- [ ] add a small preset/legend helper so repeated deploy-incident-recovery stories can be exported with less CLI repetition

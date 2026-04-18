# log-analyzer checklist

## Current slice (2026-04-18 16:10 UTC run)
- [x] resume the queued comparison-card follow-up after confirming `main` matches `origin/main`
- [x] finish dedicated `--facet-compare-card-svg` / `--facet-compare-card-html` exports built from `--facet-compare-*` output
- [x] add helper/CLI regression coverage for comparison-card rendering and export validation
- [x] generate a committed comparison-card sample artifact bundle for README/portfolio screenshots
- [x] run targeted tests, smoke checks, and 3 review passes
- [ ] run secret scan, commit, push, and write the wrap-up

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

## Current quality checks
- [x] README reflects the shipped facet flags, side-by-side comparison helpers, hotspot/time-bucket workflows, trend-card exports, comparison-card exports, and export metadata
- [x] unittest coverage includes named-field parsing, facet comparison summaries/CSV exports, comparison-card rendering, facet breakdowns, trend-card rendering, file exports, and CLI validation errors
- [x] project is resumable via review logs and wrap-up notes in `docs/`

## Next follow-up ideas
- [ ] optionally support facet-aware ranking summaries for top IP/path tables when richer custom log formats include deployment labels
- [ ] add compact annotation/callout controls so trend cards can optionally pin deploy markers or incident labels onto selected buckets
- [ ] consider dedicated comparison-card SVG/HTML artifacts built from `--facet-compare-*` output for release-review screenshots

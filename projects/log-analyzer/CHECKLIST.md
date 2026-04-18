# log-analyzer checklist

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

## Current quality checks
- [x] README reflects the shipped facet flags, side-by-side comparison helpers, hotspot/time-bucket workflows, trend-card exports, and export metadata
- [x] unittest coverage includes named-field parsing, facet comparison summaries/CSV exports, facet breakdowns, trend-card rendering, file exports, and CLI validation errors
- [x] project is resumable via review logs and wrap-up notes in `docs/`

## Next follow-up ideas
- [ ] optionally support facet-aware ranking summaries for top IP/path tables when richer custom log formats include deployment labels
- [ ] add compact annotation/callout controls so trend cards can optionally pin deploy markers or incident labels onto selected buckets
- [ ] consider dedicated comparison-card SVG/HTML artifacts built from `--facet-compare-*` output for release-review screenshots

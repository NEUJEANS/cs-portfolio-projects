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

## Current quality checks
- [x] README reflects the shipped facet flags, hotspot/time-bucket workflows, and export metadata
- [x] unittest coverage includes named-field parsing, facet breakdowns, facet CSV metadata, and CLI validation errors
- [x] project is resumable via review logs and wrap-up notes in `docs/`

## Next follow-up ideas
- [ ] generate ready-to-embed SVG/HTML mini trend cards directly from exported bucket data
- [ ] add comparison helpers that diff two facet values (for example `prod` vs `staging`) side by side for release reviews
- [ ] optionally support facet-aware ranking summaries for top IP/path tables when richer custom log formats include deployment labels

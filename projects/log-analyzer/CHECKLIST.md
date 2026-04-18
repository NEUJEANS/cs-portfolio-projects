# log-analyzer checklist

## Completed slices
- [x] parse common and combined access-log formats
- [x] summarize status, method, IP, path, referrer, and user-agent counts
- [x] normalize request-latency values and export summary CSV output
- [x] parse Nginx `request_time=` / `upstream_response_time=` fields and export hotspot CSVs
- [x] add hotspot status/method drill-down filters with self-describing JSON/CSV metadata
- [x] add inclusive `--window-start` / `--window-end` filtering with matched/excluded counts and export metadata

## Current quality checks
- [x] README reflects the shipped CLI flags and output metadata
- [x] unittest coverage includes timestamp parsing, time-window filtering, CSV metadata, and CLI validation errors
- [x] project is resumable via review logs and wrap-up notes in `docs/`

## Next follow-up ideas
- [ ] add timestamp-bucket exports (minute/hour buckets) for charts and screenshot-ready trend cards
- [ ] optionally group hotspot exports by deployment/environment labels from richer custom log formats

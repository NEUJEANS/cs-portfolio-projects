# Log Analyzer Checklist

## Facet comparison slice (2026-04-18 15:10 UTC run)
- [x] confirm repo sync before editing and preserve the existing unfinished local comparison work
- [x] choose the queued follow-up around side-by-side `prod` vs `staging` release-review comparisons
- [x] update checklist/docs so the slice is resumable
- [x] add `--facet-compare-field` and `--facet-compare-values` analysis support without disturbing the existing global/facet outputs
- [x] expose comparison summaries in text/JSON plus aligned per-bucket deltas when `--time-bucket` is active
- [x] add `--facet-compare-csv` export support and summary CSV metadata for downstream spreadsheet/report workflows
- [x] extend tests for analysis behavior, text output, CSV exports, JSON output, and CLI validation
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider a follow-up slice for comparison-card SVG/HTML exports or annotation callouts

## Hotspot filter slice (2026-04-18 09:45 UTC run)
- [x] confirm repo sync before editing
- [x] choose the queued follow-up around status/method-filtered hotspot drill-downs
- [x] do a short parser/filter refresh and self-test plan before coding
- [x] update checklist/docs so the slice is resumable
- [x] add repeatable `--hotspot-status` and `--hotspot-method` CLI flags for incident-style hotspot drill-downs
- [x] keep global request/upstream summary metrics unfiltered while applying filters only to per-path hotspot breakdowns and exports
- [x] expose active hotspot filters in text output, JSON output, and hotspot CSV metadata columns
- [x] extend tests for filtered breakdown behavior, JSON output, CSV exports, and CLI validation
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider a follow-up slice for time-window drill-downs or timestamp-aware hotspot bucketing

## Nginx timing fields slice (2026-04-18 09:02 UTC run)
- [x] confirm repo sync before editing
- [x] choose the queued follow-up around parsing named Nginx timing fields instead of starting a different project
- [x] do a short Nginx timing-field semantics refresh and self-test plan before coding
- [x] update checklist/docs so the slice is resumable
- [x] parse trailing `request_time=` and `upstream_response_time=` fields after common/combined access-log lines
- [x] treat `request_time=` as the primary request-latency source while preserving legacy unnamed latency parsing
- [x] add an upstream latency summary and aggregate retry-style multi-value upstream timings per request
- [x] extend tests for parser behavior plus text/JSON/CSV output coverage
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider per-path upstream hotspot exports in a future run

## Upstream hotspot slice (2026-04-18 09:33 UTC run)
- [x] confirm repo sync before editing
- [x] choose the queued follow-up around per-path upstream latency hotspots
- [x] do a brief upstream timing semantics refresh and self-test plan before coding
- [x] update checklist/docs so the slice is resumable
- [x] add per-path upstream latency hotspot summaries to the analyzer result and text report
- [x] add machine-friendly upstream hotspot export support for CLI workflows
- [x] extend parser/output tests for JSON, text, and CSV coverage
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider a follow-up slice for status-filtered hotspot drill-downs

- [x] inspect current parser and tests
- [x] choose one meaningful upgrade slice
- [x] add research note
- [x] add short refresh/self-test note
- [x] replace loose parsing with structured log parsing
- [x] add richer metrics: methods, paths, bytes, invalid-line count
- [x] improve CLI output modes and options
- [x] expand automated tests
- [x] run tests
- [x] run 3 review passes and fix issues found
- [x] add support for combined logs with referrer/user-agent capture
- [x] add optional latency summaries when logs include response-time fields
- [x] export CSV summaries for spreadsheet/chart workflows
- [x] add per-path latency breakdowns so slow endpoints stand out directly in the report
- [x] future slice: parse named timing fields such as `request_time=` and `upstream_response_time=` from richer Nginx-style access logs

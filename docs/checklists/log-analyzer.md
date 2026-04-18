# Log Analyzer Checklist

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
- [ ] run secret scan before push
- [ ] commit, push, and add wrap-up
- [ ] consider per-path upstream hotspot exports in a future run

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
- [ ] future slice: parse named timing fields such as `request_time=` and `upstream_response_time=` from richer Nginx-style access logs

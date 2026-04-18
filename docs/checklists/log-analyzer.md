# Log Analyzer Checklist

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

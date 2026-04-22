# Log Analyzer Checklist

## Card PNG slice (2026-04-22 03:28 UTC run)
- [x] confirm repo sync before editing and continue the queued log-analyzer card-artifact follow-up instead of starting a different project
- [x] do a brief Chrome headless / Python `tempfile` research check because PNG exports were the next highest-value artifact gap
- [x] do a short PNG capture/self-test plan before coding
- [x] update checklist/docs so the slice is resumable
- [x] add standalone `--time-bucket-card-png` and `--facet-compare-card-png` exports without branching into a second card-rendering path
- [x] add shared Chrome capture controls plus safe temporary-HTML handling for PNG-only runs
- [x] extend automated coverage for PNG helpers, CLI success, and validation errors
- [x] refresh the committed sample artifacts so annotated PNG cards are reproducible from repo state
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider raster-ready gallery/detail-bundle exports next

## Facet ranking detail-bundle slice (2026-04-19 20:21 UTC run)
- [x] confirm repo sync before editing and continue the queued log-analyzer facet-artifact follow-up instead of starting a different project
- [x] do a brief Python `zipfile` research check because deterministic download packets were the next highest-value gallery follow-up
- [x] do a short focused-page/self-test plan before coding
- [x] update checklist/docs so the slice is resumable
- [x] add `--facet-ranking-detail-bundle-dir` without branching into a second analysis path
- [x] emit a self-contained bundle index, manifest JSON, deterministic ZIP packet, and focused per-slice HTML pages with gallery back-links when available
- [x] extend automated coverage for bundle generation, ZIP determinism, CLI success, and missing-`--facet-field` validation
- [x] refresh the committed sample log/artifacts so the downloadable bundle is reproducible from repo state
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider raster-ready focused-slice exports or PNG helpers next

## Facet ranking gallery deep-link slice (2026-04-19 04:12 UTC run)
- [x] confirm repo sync before editing and continue the queued log-analyzer gallery follow-up instead of starting a different project
- [x] do a brief URL-state research check because the previous wrap-up already scoped deep links as the next highest-value slice
- [x] do a short browser URL-state refresh and self-test plan before coding
- [x] update checklist/docs so the slice is resumable
- [x] mirror search/sort/filter/hide-empty state into the gallery URL so committed artifacts can share exact views
- [x] add per-slice focused deep links plus copy/clear affordances so reviewers can jump directly to one facet card
- [x] extend automated coverage for gallery deep-link hooks and shareable-view controls
- [x] refresh the committed sample log/artifacts so the deep-linkable gallery is reproducible from repo state
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider downloadable per-facet detail bundles next

## Facet ranking gallery slice (2026-04-19 03:04 UTC run)
- [x] confirm repo sync before editing and continue the queued log-analyzer gallery follow-up instead of starting a different project
- [x] update checklist/docs so the slice is resumable
- [x] add `--facet-ranking-gallery-html` plus repeatable `--facet-ranking-gallery-link` support on top of the existing per-facet ranking data
- [x] keep gallery generation browser-friendly and portable by grouping tables per facet slice and rewriting local related links relative to the output path
- [x] extend automated coverage for gallery formatting, CLI success paths, and validation errors
- [x] refresh the committed sample log/artifacts so the gallery is reproducible from repo state
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider a follow-up slice for PNG export helpers or gallery filtering/grouping controls

## Referrer/user-agent facet ranking slice (2026-04-19 02:54 UTC run)
- [x] confirm repo sync before editing and continue the queued log-analyzer follow-up instead of starting a different project
- [x] update checklist/docs so the slice is resumable
- [x] extend facet-aware ranking outputs to referrer and user-agent fields that are already parsed from combined logs
- [x] add `--top-referrer-facet-csv` and `--top-user-agent-facet-csv` exports using the existing facet ranking schema
- [x] refresh the committed sample log/artifacts so the new CSVs are reproducible from repo state
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider a follow-up slice for referrer/user-agent comparison cards or PNG exports

## Preset gallery slice (2026-04-19 01:40 UTC run)
- [x] confirm repo sync before editing and continue the queued log-analyzer follow-up instead of starting a different project
- [x] update checklist/docs so the slice is resumable
- [x] add `--card-annotation-preset-gallery-html` so preset helper output can become a browser-friendly static artifact without a logfile
- [x] add repeatable `--card-annotation-preset-gallery-link LABEL=TARGET` support so the gallery can point at committed helper outputs, custom preset JSON, and annotated card artifacts
- [x] keep gallery generation compatible with built-in presets, custom preset files, and optional preview expansions
- [x] extend automated coverage for gallery formatting, CLI success paths, and validation errors
- [x] regenerate committed sample helper artifacts including the new gallery HTML and refreshed multi-preview JSON
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider a follow-up slice for PNG export helpers or gallery grouping/filter controls

## Custom annotation preset-file slice (2026-04-19 00:31 UTC run)
- [x] confirm repo sync before editing and continue the queued log-analyzer follow-up instead of starting a different project
- [x] update checklist/docs so the slice is resumable
- [x] add `--card-annotation-preset-file` support so custom JSON-defined stories can extend the built-in preset set
- [x] keep custom preset expansion compatible with existing trend-card and comparison-card annotation rendering/output
- [x] extend automated coverage for preset-file loading, CLI success paths, and validation errors
- [x] regenerate committed annotated sample artifacts plus README examples using a committed custom preset file
- [x] run targeted tests and smoke checks
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider a follow-up slice for gallery index pages, PNG export helpers, or preset-listing helpers

## Facet comparison card slice (2026-04-18 15:55 UTC run)
- [x] confirm repo sync before editing and preserve the existing unfinished local comparison-card work
- [x] choose the queued follow-up around dedicated comparison-card SVG/HTML artifacts instead of starting a different project
- [ ] add/update checklist + docs notes so the slice stays resumable
- [ ] finish the comparison-card SVG/HTML rendering path and CLI export flags
- [ ] add automated coverage for comparison-card helpers and CLI export validation
- [ ] generate a committed sample release-review artifact bundle for README/portfolio screenshots
- [ ] run targeted tests and smoke checks
- [ ] run at least 3 review passes and fix issues found
- [ ] run secret scan before push
- [ ] commit, push, and add wrap-up
- [ ] consider a follow-up slice for trend-card annotations/callouts

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

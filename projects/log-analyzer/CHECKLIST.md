# log-analyzer checklist

## Current slice (2026-04-19 03:53 UTC run)
- [x] resume the next `log-analyzer` follow-up after confirming `main` still matches `origin/main`
- [x] keep building on the unpublished facet-ranking gallery work already present in the repo instead of starting a different project
- [x] stamp facet-ranking rows with per-slice request-volume metadata so gallery cards can sort and summarize by actual traffic
- [x] add self-contained gallery controls for search, exact per-field filtering, sort presets, and hide-empty presentation cleanup without adding dependencies
- [x] refresh README/checklist/research/learning/review docs and regenerate the committed `docs/artifacts/log-analyzer/facet-ranking-gallery.html` sample
- [x] run targeted tests, real CLI/export smoke checks, browser validation, and 3 review passes
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
- [x] add built-in `--card-annotation-preset` story recipes for deploy/incident/recovery and deploy/rollback/recovery card exports
- [x] add JSON-backed `--card-annotation-preset-file` support for reusable custom preset aliases/files beyond the built-in stories
- [x] add gallery-level search/filter/sort/hide-empty controls plus per-slice request-volume metadata so facet-heavy ranking artifacts stay usable as the sample set grows

## Current quality checks
- [x] README reflects the shipped facet flags, side-by-side comparison helpers, hotspot/time-bucket workflows, trend-card exports, comparison-card exports, annotation controls, and custom preset-file schema
- [x] unittest coverage includes named-field parsing, facet comparison summaries/CSV exports, comparison-card rendering, annotation-aware card rendering, preset-file loading, file exports, and CLI validation errors
- [x] project is resumable via review logs, committed artifacts, and wrap-up notes in `docs/`

## Next follow-up ideas
- [ ] consider facet-aware comparison cards or gallery views for referrer/user-agent heavy release reviews beyond the current ranking-focused page
- [ ] consider PNG export helpers for cases where slide decks or chat uploads prefer raster artifacts over SVG/HTML
- [ ] consider downloadable per-facet detail bundles or deep links once the gallery controls settle

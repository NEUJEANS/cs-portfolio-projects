# log-analyzer checklist

## Current slice (2026-04-23 06:32 UTC run)
- [x] resume the queued `log-analyzer` facet gallery/detail PNG follow-up after confirming `main` still matches `origin/main`
- [x] keep building on the existing facet-ranking gallery/detail artifacts instead of switching projects because raster-ready screenshots were the clearest remaining presentation gap
- [x] do a brief Chrome headless research refresh plus a short screenshot self-test plan before coding
- [x] update checklist/docs so the slice is resumable
- [x] add `--facet-ranking-gallery-png` so the committed ranking gallery can ship as a screenshot-ready PNG alongside the HTML artifact
- [x] add `--facet-ranking-detail-bundle-pngs` so the bundle index and focused slice pages can emit deterministic PNG snapshots under `screenshots/`
- [x] extend automated coverage for gallery/detail PNG success paths, manifest/ZIP contents, and validation errors
- [x] refresh README/checklists/research/learning/review docs and regenerate committed sample gallery/detail-bundle PNG artifacts
- [x] run targeted tests, real CLI/export smoke checks, and 3 review passes
- [x] run secret scan before push
- [ ] commit, push, and write the wrap-up

## Previous slice (2026-04-22 03:28 UTC run)
- [x] resume the next `log-analyzer` follow-up after confirming `main` still matches `origin/main`
- [x] keep building on the existing card artifacts instead of switching projects because PNG/raster exports were the clearest queued gap
- [x] do a brief Chrome headless + Python `tempfile` research check plus a short PNG capture/self-test plan before coding
- [x] update checklist/docs so the slice is resumable
- [x] add standalone `--time-bucket-card-png` and `--facet-compare-card-png` exports on top of the existing card pipeline without duplicating trend/comparison analysis
- [x] add shared Chrome capture controls plus safe temporary-HTML handling for PNG-only runs
- [x] extend automated coverage for PNG helpers, CLI success, and validation errors
- [x] refresh README/checklist/research/learning/review docs and regenerate committed sample PNG artifacts alongside the existing annotated HTML/SVG cards
- [x] run targeted tests, real CLI/export smoke checks, and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and write the wrap-up

## Previous slice (2026-04-19 20:21 UTC run)
- [x] resume the next `log-analyzer` follow-up after confirming `main` still matches `origin/main`
- [x] keep building on the facet-ranking artifacts instead of switching projects because downloadable per-facet detail bundles were the clearest queued gap
- [x] do a brief Python `zipfile` research check plus a short focused-page/self-test plan before coding
- [x] add `--facet-ranking-detail-bundle-dir` on top of the existing facet-ranking/gallery pipeline without duplicating the analysis path
- [x] emit a self-contained bundle index, manifest JSON, deterministic ZIP packet, and focused per-slice HTML pages with gallery back-links when a gallery export is present
- [x] extend automated coverage for bundle generation, ZIP determinism, CLI success, and missing-`--facet-field` validation
- [x] refresh README/checklist/research/learning/review docs and regenerate the committed `docs/artifacts/log-analyzer/facet-ranking-detail-bundle/` sample bundle alongside the gallery artifact
- [x] run targeted tests, real CLI/export smoke checks, and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and write the wrap-up

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
- [x] add PNG export helpers for cases where slide decks or chat uploads prefer raster artifacts over SVG/HTML
- [x] add raster-ready focused-slice exports or screenshot helpers for facet-ranking galleries/detail bundles now that trend/comparison card PNG exports exist
- [ ] consider lightweight summary tiles or scorecards for the facet gallery/bundle index so overview screenshots explain busiest slices faster
- [ ] consider optional contact-sheet style multi-slice PNG exports for large facet bundles where reviewers want one raster sheet instead of opening each focused page

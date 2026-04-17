# Mini MapReduce watermark late-summary slice (2026-04-17 21:01 UTC run)

- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] do brief web research on event-time watermarks / allowed lateness semantics to keep the plugin story grounded in real streaming terminology
- [x] do a short Python `datetime` / event-time self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add a bundled `plugins_watermark_late_summary.py` example that summarizes accepted late events, dropped late events, and hottest replay windows from `stream,event_time,arrival_time,value` rows
- [x] give the new plugin deterministic benchmark families plus structured replay/backfill hotspot annotations
- [x] extend project-level and repo-level tests for watermark summary output, benchmark metadata, and catalog discovery
- [x] regenerate the committed Mini MapReduce artifact bundle so the catalog, plugin pages, diff report, sensor-backfill benchmark report, and docs index include the new plugin
- [x] run targeted tests and 3 review passes
- [x] run secret scan before push
- [ ] commit, push, and add wrap-up

## Review notes
- review pass 1: fixed project checklist + README drift so the new watermark plugin is documented in the same way as the service-latency, sessionization, and streaming-window examples.
- review pass 2: regenerated the docs bundle, caught the empty `docs-index.json` mistake from a redirected CLI run, then fixed it and regenerated again after the feature commit so commit-pinned GitHub links resolve to a commit that actually contains the new plugin.
- review pass 3: reran `py_compile`, both unittest entry points, a docs-index link audit, and an absolute-path leak audit; all checks passed.

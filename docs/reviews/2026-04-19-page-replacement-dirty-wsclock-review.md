# Review log — page-replacement dirty WSClock slice

Date: 2026-04-19

## Pass 1 — CLI wiring audit
### Findings
- `--dirty-page` / `--dirty-pages-file` existed in the parser but were not threaded through `compare`, `study`, `gallery`, `aggregate`, or `trace-compare`.
- This caused feature drift: core simulation code knew about dirty pages, but several commands still behaved like the old clean-page-only model.

### Fixes
- resolved dirty-page args once in `main()`
- passed dirty-page config through every relevant command path
- added dirty-page metadata to JSON/text outputs for simulate and compare

## Pass 2 — artifact/report audit
### Findings
- trace-compare outputs were still page-fault-centric and hid the new writeback metric
- gallery JSON did not expose dirty-page metadata or per-workload WSClock writeback averages

### Fixes
- added dirty-page lines to trace-compare text output
- added left/right average writeback columns to trace-compare Markdown/HTML
- added dirty-page metadata plus `average_wsclock_writebacks` to gallery JSON output

## Pass 3 — regression/docs audit
### Findings
- tests still expected the older CSV schemas without `wsclock_writebacks` / `wsclock_avg_writebacks`
- README/checklist still described WSClock as a clean-page approximation and did not document the new dirty-page demo flow

### Fixes
- updated unit tests for the expanded schemas and added focused dirty-page regression coverage
- refreshed README + project checklist
- added a committed dirty-page benchmark artifact bundle and reusable dirty-page sample file

## Result
The slice now behaves consistently across simulation, exported artifacts, docs, and regression tests.

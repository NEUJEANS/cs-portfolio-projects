# Page Replacement Lab Checklist

## 2026-04-18 initial vertical slice
- [x] choose a new project because the current set is already broadly complete
- [x] do brief page-replacement research and pick a strong reference workload
- [x] do a short paging/Belady refresh and self-test
- [x] implement FIFO, LRU, and OPT simulators
- [x] add CLI commands for single-run simulation, comparison, and frame-range study
- [x] add JSON output and readable text reports
- [x] add README with usage examples and interview notes
- [x] add tests
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [ ] commit and push
- [ ] append wrap-up

## 2026-04-18 clock + presets slice
- [x] do brief research on Clock / second-chance and locality-friendly preset workloads
- [x] do a short refresh on Clock reference-bit behavior and stack-algorithm expectations
- [x] add project-local checklist markdown for resumable follow-up work
- [x] implement Clock / second-chance replacement
- [x] add built-in workload presets plus preset-listing CLI support
- [x] extend frame-range study output to surface non-FIFO regressions too
- [x] refresh README usage examples and interview notes
- [x] add regression tests for Clock + preset flows
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [ ] commit and push
- [ ] append wrap-up

## 2026-04-18 gallery slice
- [x] do brief research on semantic figure/caption markup and inline SVG accessibility IDs
- [x] do a short refresh on static HTML gallery patterns and unique SVG metadata IDs
- [x] update checklist markdown so the slice stays resumable
- [x] implement a `gallery` command that batches the built-in preset studies
- [x] write Markdown / SVG / CSV / JSON companions per preset in one run
- [x] generate a committed static HTML gallery with inline SVG cards and download links
- [x] refresh README artifact examples and future follow-up notes
- [x] add regression tests for gallery generation and SVG ID uniqueness
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [ ] commit and push
- [ ] append wrap-up

## 2026-04-18 trace benchmark slice
- [x] do brief research on phase shifts, hot sets, and scan-heavy trace behavior
- [x] do a short refresh on workload locality patterns and benchmark-driven page-replacement evaluation
- [x] update checklist markdown so the slice stays resumable
- [x] add larger built-in trace benchmark bundles and benchmark-listing CLI support
- [x] extend compare/study/gallery flows to accept benchmark inputs alongside presets
- [x] generate committed mixed gallery artifacts for presets plus the heavier trace bundles
- [x] refresh README and learning notes for the new benchmark workflows
- [x] add regression tests for benchmark parsing, listing, and mixed gallery generation
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [ ] commit and push
- [ ] append wrap-up

## 2026-04-18 aging slice
- [x] do brief research on aging counters and reference-bit history
- [x] do a short refresh on how aging approximates LRU without exact timestamps
- [x] update checklist markdown so the slice stays resumable
- [x] implement an aging page-replacement policy
- [x] thread aging through compare / study / gallery / CSV / SVG / JSON outputs
- [x] refresh README, learning notes, and committed page-replacement artifacts
- [x] add regression tests for aging behavior and dynamic report outputs
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [ ] commit and push
- [ ] append wrap-up

## 2026-04-18 trace-summary slice
- [x] verify git sync state before editing
- [x] do brief reuse-distance / working-set / phase-hint research
- [x] write a short trace-summary refresh note
- [x] update resumable project checklist state
- [x] implement a `trace-summary` command for preset / benchmark / custom inputs
- [x] export a committed benchmark trace-summary artifact
- [x] refresh README, checklist notes, and artifact references
- [x] add regression tests for trace-summary summaries and Markdown output
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-18 aggregate-dashboard slice
- [x] verify git sync state before editing
- [x] decide that extra web research is not needed for this reporting-focused slice
- [x] write a short normalization / aggregate-dashboard refresh note
- [x] update resumable project checklist state
- [x] implement an `aggregate` command for cross-workload comparison dashboards
- [x] export committed aggregate CSV / SVG / JSON / HTML artifacts
- [x] refresh README, checklist notes, and artifact references
- [x] add regression tests for aggregate dashboard output paths and JSON summaries
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-18 trace-cards slice
- [x] verify git sync state before editing
- [x] decide that extra web research is not needed for this reporting-focused slice
- [x] write a short trace-card refresh note
- [x] update resumable project checklist state
- [x] extend `trace-summary` with SVG / HTML artifact exports
- [x] export committed compiler benchmark trace-summary card artifacts
- [x] refresh README and committed page-replacement artifact references
- [x] add regression tests for trace-summary SVG / HTML outputs
- [x] run tests and real smoke commands
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 custom-aggregate slice
- [x] verify git sync state before editing
- [x] decide that extra web research is not needed for this CLI/reporting-focused slice
- [x] write a short aggregate custom-trace refresh note
- [x] update resumable project checklist state
- [x] implement repeated `aggregate --pages-file` support for imported custom traces
- [x] export committed mixed aggregate CSV / SVG / JSON / HTML artifacts with one imported trace
- [x] refresh README and committed page-replacement artifact references
- [x] add regression tests for custom aggregate workload selection and JSON summaries
- [x] run tests and real smoke commands
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 gallery custom-trace slice
- [x] verify git sync state before editing
- [x] decide that extra web research is not needed for this CLI/reporting-focused slice
- [x] write a short gallery custom-trace refresh note
- [x] update resumable project checklist state
- [x] extend `gallery --pages-file` so imported workloads generate per-workload trace-summary drill-down cards
- [x] export committed mixed gallery CSV / SVG / JSON / HTML artifacts with one imported trace
- [x] refresh README and committed page-replacement artifact references
- [x] add regression tests for custom gallery workload selection and trace-summary bundle paths
- [x] run tests and real smoke commands
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 imported trace-compare slice
- [x] verify git sync state before editing
- [x] decide that extra web research is not needed for this CLI/reporting-focused slice
- [x] write a short imported trace-comparison refresh note
- [x] update resumable project checklist state
- [x] implement a dedicated `trace-compare` command for exactly two imported traces
- [x] export committed Markdown / SVG / CSV / JSON / HTML comparison artifacts for the sample custom traces
- [x] refresh README, project checklist, and committed artifact references
- [x] add regression tests for trace-compare output and argument validation
- [x] run tests and real smoke commands
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 WSClock slice
- [x] verify git sync state before editing
- [x] do brief WSClock / working-set research
- [x] write a short WSClock refresh note
- [x] update resumable project checklist state
- [x] implement a simplified clean-page `wsclock` replacement policy
- [x] thread WSClock through compare / study / gallery / aggregate / trace-compare outputs
- [x] refresh README and committed page-replacement artifact references
- [x] add regression tests for WSClock behavior and dynamic report outputs
- [x] run tests and real smoke commands
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 WSClock window slice
- [x] verify git sync state before editing
- [x] do brief WSClock tau / working-set-window research
- [x] write a short WSClock window refresh note
- [x] update resumable project checklist state
- [x] implement a configurable `--wsclock-window` override across the CLI surface
- [x] thread WSClock window metadata through study / gallery / aggregate / trace-compare artifacts
- [x] refresh README and project checklist docs for the new tuning workflow
- [x] add regression tests for WSClock window overrides and artifact columns
- [x] run tests and real smoke commands
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 WSClock tuning slice
- [x] verify git sync state before editing
- [x] do brief WSClock tau / dirty-page writeback research
- [x] write a short WSClock tuning refresh note
- [x] update resumable project checklist state
- [x] implement a `tune-wsclock` CLI that sweeps candidate windows and recommends a weighted score winner
- [x] export committed Markdown / CSV / JSON tuning artifacts for the dirty compiler benchmark scenario
- [x] refresh README and project checklist docs for the new tuning workflow
- [x] add regression tests for tuning JSON plus Markdown / CSV exports
- [x] run tests and real smoke commands
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 WSClock adaptive slice
- [x] verify git sync state before editing
- [x] decide that extra web research is not needed for this WSClock follow-on heuristic slice
- [x] write a short adaptive-WSClock refresh note
- [x] update resumable project checklist state
- [x] implement a `compare-wsclock-modes` CLI that compares auto-fixed, tuned-fixed, and adaptive WSClock `tau` choices
- [x] add a benchmark trace crafted to show an adaptive-win scenario
- [x] export committed Markdown / CSV / JSON / text fixed-vs-adaptive artifacts for both a clear win and a realistic tie case
- [x] refresh README and project checklist docs for the adaptive workflow
- [x] add regression tests for mode comparison output plus explicit adaptive-window bounds
- [x] run tests and real smoke commands
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 WSClock frame-budget study slice
- [x] verify git sync state before editing
- [x] decide that extra web research is not needed for this WSClock reporting follow-on slice
- [x] write a short frame-budget-study refresh note
- [x] update resumable project checklist state
- [x] implement a `study-wsclock-modes` CLI that summarizes adaptive-vs-fixed outcomes across a frame range
- [x] export committed Markdown / SVG / CSV / JSON / text frame-budget study artifacts for both an adaptive-win benchmark and an honest tie-or-loss benchmark
- [x] refresh README and project checklist docs for the multi-frame adaptive workflow
- [x] add regression tests for study summary output plus Markdown / SVG / CSV exports
- [x] run tests and real smoke commands
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [ ] commit and push
- [ ] append wrap-up

# page-replacement-lab checklist

## Completed slices
- [x] initial FIFO / LRU / OPT simulator with compare and frame-range study commands
- [x] JSON output and deterministic step traces for explainable runs
- [x] Clock / second-chance replacement policy
- [x] built-in workload presets for repeatable demos and locality comparisons
- [x] frame-range studies that report FIFO Belady anomalies plus other algorithm regressions
- [x] screenshot-ready study artifact exports (Markdown / SVG / CSV) for page-fault-vs-frame summaries
- [x] multi-workload HTML gallery generation with per-preset Markdown / SVG / CSV / JSON bundles
- [x] regression coverage for preset input, preset listing, Clock counts, and mixed-input validation
- [x] regression coverage for study artifact export paths and generated report content
- [x] regression coverage for gallery bundle generation and unique inline-SVG accessibility IDs
- [x] larger trace-file benchmark bundles beyond the small built-in presets, including benchmark listing, benchmark-aware compare/study flows, and mixed gallery exports
- [x] trace-summary SVG / HTML card exports for slide-ready locality summaries
- [x] gallery support for imported custom traces with per-workload trace-summary drill-down cards
- [x] regression coverage for imported gallery workloads and trace-summary bundle paths
- [x] simplified clean-page WSClock policy threaded through compare / study / gallery / aggregate / trace-compare outputs
- [x] tunable WSClock working-set window (`--wsclock-window`) propagated through CLI output and exported artifacts
- [x] dirty-page-aware WSClock inputs (`--dirty-page`, `--dirty-pages-file`) plus writeback tracking across compare / study / gallery / aggregate / trace-compare outputs
- [x] WSClock `tau` sweep / recommendation workflow with `tune-wsclock` Markdown / CSV / JSON exports

## Current demo-ready flow
- [x] list built-in workloads and larger trace benchmarks for an interview or portfolio walkthrough
- [x] simulate one policy with `--show-steps` on a preset workload
- [x] compare FIFO / Clock / Aging / WSClock / LRU / OPT on either a compact preset or a larger benchmark trace
- [x] mark dirty/write-heavy pages for WSClock sensitivity demos with explicit writeback counts
- [x] tune a fixed WSClock `tau` with a weighted page-fault/writeback sweep for one workload and frame budget
- [x] compare fixed-window and adaptive WSClock `tau` choices with tie-aware reporting for one workload/frame budget
- [x] study multiple frame counts and call out FIFO anomalies or Clock regressions
- [x] export JSON for downstream charts or frontend demos
- [x] export Markdown / SVG / CSV study artifacts for screenshots and portfolio cards
- [x] generate a browsable gallery that bundles built-in presets, larger benchmark traces, and imported custom traces into one static HTML artifact page
- [x] export trace-summary Markdown / SVG / HTML artifacts for a benchmark or imported workload
- [x] link imported gallery workloads to their own drill-down trace-summary cards
- [x] compare exactly two imported traces side by side with one portfolio-ready artifact bundle

## Next vertical slices
- [x] add aging-style page replacement for stronger systems realism
- [x] add working-set style policies for stronger systems realism
- [x] add dirty-page-aware WSClock refinement with dirty-bit-aware cleaning and writeback tracking
- [x] add a WSClock `tau` tuning / recommendation sweep for workload-specific analysis
- [x] compare fixed-window WSClock recommendations against an adaptive `tau` heuristic
- [x] add cross-workload aggregate comparison charts for slide-ready summaries
- [x] add a trace-summary or reuse-distance helper for imported workloads
- [x] add SVG/HTML trace-summary cards for portfolio slides
- [x] add side-by-side imported-trace comparisons
- [ ] export adaptive-vs-fixed WSClock comparisons across multiple frame budgets or gallery cards

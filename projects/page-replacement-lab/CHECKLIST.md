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

## Current demo-ready flow
- [x] list built-in workloads and larger trace benchmarks for an interview or portfolio walkthrough
- [x] simulate one policy with `--show-steps` on a preset workload
- [x] compare FIFO / Clock / Aging / LRU / OPT on either a compact preset or a larger benchmark trace
- [x] study multiple frame counts and call out FIFO anomalies or Clock regressions
- [x] export JSON for downstream charts or frontend demos
- [x] export Markdown / SVG / CSV study artifacts for screenshots and portfolio cards
- [x] generate a browsable gallery that bundles built-in presets plus larger benchmark traces into one static HTML artifact page

## Next vertical slices
- [x] add aging-style page replacement for stronger systems realism
- [ ] add working-set style policies for stronger systems realism
- [ ] add cross-workload aggregate comparison charts for slide-ready summaries
- [x] add a trace-summary or reuse-distance helper for imported workloads
- [ ] add SVG/HTML trace-summary cards or side-by-side imported-trace comparisons

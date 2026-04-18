# page-replacement-lab checklist

## Completed slices
- [x] initial FIFO / LRU / OPT simulator with compare and frame-range study commands
- [x] JSON output and deterministic step traces for explainable runs
- [x] Clock / second-chance replacement policy
- [x] built-in workload presets for repeatable demos and locality comparisons
- [x] frame-range studies that report FIFO Belady anomalies plus other algorithm regressions
- [x] screenshot-ready study artifact exports (Markdown / SVG / CSV) for page-fault-vs-frame summaries
- [x] regression coverage for preset input, preset listing, Clock counts, and mixed-input validation
- [x] regression coverage for study artifact export paths and generated report content

## Current demo-ready flow
- [x] list built-in workloads for an interview or portfolio walkthrough
- [x] simulate one policy with `--show-steps` on a preset workload
- [x] compare FIFO / Clock / LRU / OPT on the same preset
- [x] study multiple frame counts and call out FIFO anomalies or Clock regressions
- [x] export JSON for downstream charts or frontend demos
- [x] export Markdown / SVG / CSV study artifacts for screenshots and portfolio cards

## Next vertical slices
- [ ] add larger trace-file benchmark bundles beyond the small built-in presets
- [ ] add aging or working-set style policies for stronger systems realism
- [ ] add an HTML artifact gallery that bundles multiple study cards for side-by-side browsing

# page-replacement-lab checklist

## Completed slices
- [x] initial FIFO / LRU / OPT simulator with compare and frame-range study commands
- [x] JSON output and deterministic step traces for explainable runs
- [x] Clock / second-chance replacement policy
- [x] built-in workload presets for repeatable demos and locality comparisons
- [x] frame-range studies that report FIFO Belady anomalies plus other algorithm regressions
- [x] regression coverage for preset input, preset listing, Clock counts, and mixed-input validation

## Current demo-ready flow
- [x] list built-in workloads for an interview or portfolio walkthrough
- [x] simulate one policy with `--show-steps` on a preset workload
- [x] compare FIFO / Clock / LRU / OPT on the same preset
- [x] study multiple frame counts and call out FIFO anomalies or Clock regressions
- [x] export JSON for downstream charts or frontend demos

## Next vertical slices
- [ ] add chart/report export helpers for page-fault-vs-frame screenshots
- [ ] add larger trace-file benchmark bundles beyond the small built-in presets
- [ ] add aging or working-set style policies for stronger systems realism

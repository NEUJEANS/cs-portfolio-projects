# Page Replacement Lab

A virtual-memory simulator for comparing classic page replacement strategies on the same reference string, with built-in workload presets and frame-range studies that surface FIFO Belady anomalies and other fault regressions.

## Why this project matters
- demonstrates operating-systems and memory-management fundamentals in runnable code
- compares practical online heuristics against the theoretical optimal baseline
- includes **Clock / second-chance** and **Aging**, showing two practical approximations that sit between pure FIFO and idealized recency tracking
- makes page-fault tradeoffs visible with deterministic step traces, reusable presets, and frame-range studies
- gives strong interview material around locality, stack algorithms, and Belady's anomaly
- includes a `trace-summary` workflow that surfaces reuse-distance buckets, sliding working-set sizes, and phase-boundary hints for imported workloads
- includes an `aggregate` dashboard workflow that normalizes page-fault rates across presets and larger benchmark traces for one slide-ready comparison view
- leaves room for future extensions like working-set replacement policies or richer trace-summary cards

## Features
- simulate **FIFO**, **Clock / second-chance**, **Aging**, **LRU**, and **OPT** page replacement
- load a reference string from repeated `--page` flags, a file, a built-in preset, or a larger built-in trace benchmark bundle
- print a step-by-step trace for one algorithm
- compare all five algorithms on the same workload
- run a frame-range study to detect FIFO Belady anomalies and other fault regressions
- list built-in workload presets for repeatable demos and screenshots
- list larger built-in trace benchmarks that model phase shifts, hot-set scans, and streaming-window bursts
- export structured JSON for reports, demos, or frontend visualizations later
- export study results as Markdown, CSV, and self-contained SVG cards for README screenshots and portfolio pages
- generate a multi-workload HTML gallery that can mix compact presets with heavier trace benchmarks and downloadable Markdown / SVG / CSV / JSON companions
- summarize imported traces with reuse-distance buckets, sliding working-set sizes, and phase-boundary hints that explain why a workload changes policy behavior
- build a cross-workload aggregate dashboard with normalized average page-fault-rate charts plus CSV / SVG / JSON / HTML artifacts

## Quick start

### List built-in workload presets
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py list-presets
```

### Simulate one algorithm with a trace
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py simulate clock --frames 3 \
  --preset classic-belady --show-steps
```

### List the larger built-in trace benchmarks
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py list-benchmarks
```

### Compare FIFO / Clock / Aging / LRU / OPT
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py compare --frames 3 \
  --preset classic-belady
```

### Compare on a heavier trace benchmark
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py compare --frames 5 \
  --benchmark compiler-phase-shift
```

### Study frame counts and flag regressions
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py study --min-frames 2 --max-frames 5 \
  --preset classic-belady
```

### Export screenshot-ready study artifacts
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py study --min-frames 2 --max-frames 6 \
  --preset classic-belady \
  --markdown-out docs/artifacts/page-replacement-lab/classic-belady-study.md \
  --svg-out docs/artifacts/page-replacement-lab/classic-belady-study.svg \
  --csv-out docs/artifacts/page-replacement-lab/classic-belady-study.csv
```

### Build a browsable gallery across presets plus larger benchmark traces
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py gallery --min-frames 3 --max-frames 8 \
  --artifact-dir docs/artifacts/page-replacement-lab/gallery \
  --include-benchmarks
```

### Summarize a heavier trace for reuse distance and phase hints
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py trace-summary \
  --benchmark compiler-phase-shift \
  --window-size 12 \
  --markdown-out docs/artifacts/page-replacement-lab/compiler-phase-shift-trace-summary.md
```

### Build an aggregate dashboard across presets plus larger trace benchmarks
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py aggregate --min-frames 3 --max-frames 8 \
  --artifact-dir docs/artifacts/page-replacement-lab/aggregate \
  --include-benchmarks
```

### Load pages from a file instead of a preset
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py compare --frames 4 \
  --pages-file workload.txt --json
```

## Built-in presets
- `classic-belady` — the standard short anomaly reference string `1 2 3 4 1 2 5 1 2 3 4 5`
- `looping-hotset` — small hot working set with a short burst page
- `scan-then-reuse` — long scan followed by a tighter reuse window
- `mixed-locality-bursts` — hot-loop bursts interrupted by colder misses

These presets make demos reproducible and help explain how locality changes policy performance.

## Built-in trace benchmarks
- `compiler-phase-shift` — larger compiler-style trace with a warm parser hot set, a code-generation scan, and optimizer bursts
- `db-hotset-scan` — dashboard-style hot pages interrupted by a longer analytics scan plus checkpoint churn
- `streaming-burst-window` — stream-processing working-set shifts with cold backfill bursts and rolling-window updates

These benchmark bundles are longer than the compact presets and better for portfolio screenshots that need stronger separation between locality-friendly and scan-heavy workloads.
Use exactly one of `--preset`, `--benchmark`, or explicit `--page` / `--pages-file` input for a given run.

## Example output
```text
frames: 3
source: preset classic-belady — classic Belady anomaly reference string that makes FIFO regress from 3 to 4 frames
reference: 1 2 3 4 1 2 5 1 2 3 4 5
algorithm  faults  hits  hit-rate
fifo       9       3      25.00%
clock      9       3      25.00%
aging      10      2      16.67%
lru        10      2      16.67%
opt        7       5      41.67%
best faults: 7 (opt)
```

## Committed artifact examples
- `docs/artifacts/page-replacement-lab/classic-belady-study.md` — narrative study report with the winner table and anomaly callouts
- `docs/artifacts/page-replacement-lab/classic-belady-study.svg` — screenshot-ready chart card for README or portfolio galleries
- `docs/artifacts/page-replacement-lab/classic-belady-study.csv` — spreadsheet/chart-friendly export of the same frame sweep
- `docs/artifacts/page-replacement-lab/gallery/index.html` — browsable multi-workload gallery with inline SVG charts and download links for each preset and benchmark bundle
- `docs/artifacts/page-replacement-lab/gallery/compiler-phase-shift-study.{md,svg,csv,json}` — committed heavier-trace benchmark bundle for the compiler phase-shift workload
- `docs/artifacts/page-replacement-lab/gallery/db-hotset-scan-study.{md,svg,csv,json}` — committed heavier-trace benchmark bundle for the dashboard/analytics scan workload
- `docs/artifacts/page-replacement-lab/gallery/streaming-burst-window-study.{md,svg,csv,json}` — committed heavier-trace benchmark bundle for the streaming-window workload
- `docs/artifacts/page-replacement-lab/compiler-phase-shift-trace-summary.{md,json}` — committed reuse-distance and phase-hint report for the compiler-style benchmark trace
- `docs/artifacts/page-replacement-lab/aggregate/index.html` — static aggregate dashboard that compares presets and benchmark traces on one normalized page-fault-rate chart
- `docs/artifacts/page-replacement-lab/aggregate/aggregate-average-fault-rate.svg` — slide-ready grouped bar chart for the aggregate dashboard
- `docs/artifacts/page-replacement-lab/aggregate/aggregate-workload-comparison.csv` — spreadsheet-friendly summary of per-workload average faults and normalized rates
- `docs/artifacts/page-replacement-lab/aggregate/aggregate-summary.json` — machine-readable aggregate payload for future frontend or notebook reuse

## Testing
```bash
python3 -m unittest discover -s projects/page-replacement-lab -p "test_*.py"
```

## Interview talking points
- explain why **OPT** is the gold-standard benchmark even though it is not implementable online
- describe how **Clock / second-chance** approximates recency using a reference bit and circular hand
- describe how **Aging** uses a shifting reference-bit history to approximate LRU with lower bookkeeping pressure than exact recency stacks
- explain why **LRU** and **OPT** are stack algorithms while **FIFO** is not
- walk through why FIFO can show Belady's anomaly and why Clock can still regress on some workloads even though it often behaves better in practice
- discuss how locality of reference changes the ranking between FIFO, Clock, Aging, and LRU
- explain how reuse distance helps estimate locality pressure and why the trace-summary report flags scan-heavy phase changes
- suggest how this simulator could extend into real trace replay, working-set analysis, or richer report/gallery generation

## Future improvements
- add working-set or WSClock-style algorithms for richer policy comparisons
- generate richer HTML gallery drill-down pages for custom traces or side-by-side policy narratives
- add SVG/HTML trace-summary cards or side-by-side imported-trace comparisons for portfolio slides
- allow custom imported traces to join the aggregate dashboard without editing source code

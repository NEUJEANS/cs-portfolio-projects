# Page Replacement Lab

A virtual-memory simulator for comparing classic page replacement strategies on the same reference string, with built-in workload presets and frame-range studies that surface FIFO Belady anomalies and other fault regressions.

## Why this project matters
- demonstrates operating-systems and memory-management fundamentals in runnable code
- compares practical online heuristics against the theoretical optimal baseline
- includes **Clock / second-chance**, **Aging**, and a simplified **WSClock** policy with a configurable working-set window, showing three practical approximations that sit between pure FIFO and idealized recency tracking
- makes page-fault tradeoffs visible with deterministic step traces, reusable presets, and frame-range studies
- gives strong interview material around locality, stack algorithms, and Belady's anomaly
- includes a `trace-summary` workflow that surfaces reuse-distance buckets, sliding working-set sizes, and phase-boundary hints for imported workloads
- includes an `aggregate` dashboard workflow that normalizes page-fault rates across presets, larger benchmark traces, and imported custom traces for one slide-ready comparison view
- includes a `trace-compare` workflow that contrasts exactly two imported traces side by side with rate charts, frame tables, and locality snapshots
- leaves room for future extensions like dirty-page-aware WSClock refinements, adaptive working-set-window heuristics, or richer narrative trace write-ups

## Features
- simulate **FIFO**, **Clock / second-chance**, **Aging**, **WSClock** (clean-page approximation with configurable `tau` / working-set window), **LRU**, and **OPT** page replacement
- load a reference string from repeated `--page` flags, a file, a built-in preset, or a larger built-in trace benchmark bundle
- print a step-by-step trace for one algorithm
- compare all six bundled algorithms on the same workload, including optional `--wsclock-window` overrides for WSClock sensitivity studies
- run a frame-range study to detect FIFO Belady anomalies and other fault regressions
- list built-in workload presets for repeatable demos and screenshots
- list larger built-in trace benchmarks that model phase shifts, hot-set scans, and streaming-window bursts
- export structured JSON for reports, demos, or frontend visualizations later
- export study results as Markdown, CSV, and self-contained SVG cards for README screenshots and portfolio pages
- generate a multi-workload HTML gallery that can mix compact presets, heavier trace benchmarks, and imported custom traces with downloadable Markdown / SVG / CSV / JSON companions
- summarize imported traces with reuse-distance buckets, sliding working-set sizes, and phase-boundary hints that explain why a workload changes policy behavior
- export trace-summary results as Markdown, slide-ready SVG cards, and browsable HTML companion pages
- build a cross-workload aggregate dashboard with normalized average page-fault-rate charts plus CSV / SVG / JSON / HTML artifacts
- compare exactly two imported traces side by side with one `trace-compare` run that emits Markdown / SVG / CSV / JSON / HTML artifacts
- mix imported `--pages-file` workloads into aggregate dashboard or gallery runs without editing the source code

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

### Compare FIFO / Clock / Aging / WSClock / LRU / OPT
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py compare --frames 3 \
  --preset classic-belady
```

### Compare on a heavier trace benchmark
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py compare --frames 5 \
  --benchmark compiler-phase-shift
```

### Compare WSClock window sensitivity on the same benchmark
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py compare --frames 5 \
  --benchmark compiler-phase-shift \
  --wsclock-window 1
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

### Mix one or more imported traces into the gallery with drill-down cards
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py gallery --min-frames 3 --max-frames 8 \
  --preset classic-belady \
  --pages-file projects/page-replacement-lab/custom-traces/mobile-app-session.txt \
  --artifact-dir docs/artifacts/page-replacement-lab/gallery
```

Repeat `--pages-file` to add more imported traces, each with its own study bundle plus trace-summary drill-down card.

Use `--wsclock-window <references>` with `simulate`, `compare`, `study`, `gallery`, `aggregate`, or `trace-compare` to override WSClock's `tau` value instead of using the default `max(4, frames * 2)` heuristic. The exported Markdown / CSV / JSON / SVG / HTML artifacts record both the chosen mode and each frame's effective WSClock window.

### Summarize a heavier trace for reuse distance and phase hints
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py trace-summary \
  --benchmark compiler-phase-shift \
  --window-size 12 \
  --markdown-out docs/artifacts/page-replacement-lab/compiler-phase-shift-trace-summary.md
```

### Export a slide-ready trace-summary SVG + HTML card
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py trace-summary \
  --benchmark compiler-phase-shift \
  --window-size 12 \
  --markdown-out docs/artifacts/page-replacement-lab/compiler-phase-shift-trace-summary.md \
  --svg-out docs/artifacts/page-replacement-lab/compiler-phase-shift-trace-summary.svg \
  --html-out docs/artifacts/page-replacement-lab/compiler-phase-shift-trace-summary.html
```

### Build an aggregate dashboard across presets plus larger trace benchmarks
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py aggregate --min-frames 3 --max-frames 8 \
  --artifact-dir docs/artifacts/page-replacement-lab/aggregate \
  --include-benchmarks
```

### Mix one or more imported traces into the aggregate dashboard
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py aggregate --min-frames 3 --max-frames 8 \
  --preset classic-belady \
  --benchmark compiler-phase-shift \
  --pages-file projects/page-replacement-lab/custom-traces/mobile-app-session.txt \
  --artifact-dir docs/artifacts/page-replacement-lab/custom-aggregate
```

Repeat `--pages-file` to add more imported traces to the same dashboard build.

### Compare two imported traces side by side
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py trace-compare --min-frames 3 --max-frames 8 \
  --pages-file projects/page-replacement-lab/custom-traces/mobile-app-session.txt \
  --pages-file projects/page-replacement-lab/custom-traces/reporting-scan-session.txt \
  --artifact-dir docs/artifacts/page-replacement-lab/trace-compare
```

`trace-compare` requires exactly two imported `--pages-file` inputs and emits one Markdown / SVG / CSV / JSON / HTML bundle for that left-vs-right comparison.

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
Use exactly one of `--preset`, `--benchmark`, or explicit `--page` / `--pages-file` input for a single-workload run. The `aggregate` and `gallery` commands can intentionally mix repeated `--preset`, `--benchmark`, and `--pages-file` selections in one dashboard build or gallery export. The dedicated `trace-compare` command instead requires exactly two imported `--pages-file` arguments.

## Example output
```text
frames: 3
source: preset classic-belady — classic Belady anomaly reference string that makes FIFO regress from 3 to 4 frames
reference: 1 2 3 4 1 2 5 1 2 3 4 5
wsclock window: auto (max(4, frames * 2)) (effective 6)
algorithm  faults  hits  hit-rate
fifo       9       3      25.00%
clock      9       3      25.00%
aging      10      2      16.67%
wsclock    10      2      16.67%
lru        10      2      16.67%
opt        7       5      41.67%
best faults: 7 (opt)
```

## Committed artifact examples
- `docs/artifacts/page-replacement-lab/classic-belady-study.md` — narrative study report with the winner table and anomaly callouts
- `docs/artifacts/page-replacement-lab/classic-belady-study.svg` — screenshot-ready chart card for README or portfolio galleries
- `docs/artifacts/page-replacement-lab/classic-belady-study.csv` — spreadsheet/chart-friendly export of the same frame sweep
- `docs/artifacts/page-replacement-lab/gallery/index.html` — browsable multi-workload gallery with inline SVG charts, benchmark bundles, and imported-trace drill-down links
- `docs/artifacts/page-replacement-lab/gallery/compiler-phase-shift-study.{md,svg,csv,json}` — committed heavier-trace benchmark bundle for the compiler phase-shift workload
- `docs/artifacts/page-replacement-lab/gallery/db-hotset-scan-study.{md,svg,csv,json}` — committed heavier-trace benchmark bundle for the dashboard/analytics scan workload
- `docs/artifacts/page-replacement-lab/gallery/streaming-burst-window-study.{md,svg,csv,json}` — committed heavier-trace benchmark bundle for the streaming-window workload
- `docs/artifacts/page-replacement-lab/gallery/mobile-app-session-study.{md,svg,csv,json}` — committed imported-trace study bundle used to demonstrate gallery-ready custom workloads
- `docs/artifacts/page-replacement-lab/gallery/mobile-app-session-trace-summary.{md,svg,html,json}` — committed drill-down card bundle for the imported mobile-app-session trace
- `docs/artifacts/page-replacement-lab/compiler-phase-shift-trace-summary.{md,json}` — committed reuse-distance and phase-hint report for the compiler-style benchmark trace
- `docs/artifacts/page-replacement-lab/compiler-phase-shift-trace-summary.svg` — slide-ready trace-summary card with reuse-distance buckets and per-window pressure charts
- `docs/artifacts/page-replacement-lab/compiler-phase-shift-trace-summary.html` — browsable trace-summary companion page with the inline SVG card plus bucket/window tables
- `docs/artifacts/page-replacement-lab/aggregate/index.html` — static aggregate dashboard that compares presets and benchmark traces on one normalized page-fault-rate chart
- `docs/artifacts/page-replacement-lab/aggregate/aggregate-average-fault-rate.svg` — slide-ready grouped bar chart for the aggregate dashboard
- `docs/artifacts/page-replacement-lab/aggregate/aggregate-workload-comparison.csv` — spreadsheet-friendly summary of per-workload average faults, source labels, and normalized rates
- `docs/artifacts/page-replacement-lab/aggregate/aggregate-summary.json` — machine-readable aggregate payload for future frontend or notebook reuse
- `docs/artifacts/page-replacement-lab/custom-aggregate/index.html` — committed mixed aggregate dashboard that includes a custom imported trace file alongside built-in workloads
- `docs/artifacts/page-replacement-lab/custom-aggregate/aggregate-summary.json` — sample mixed-workload payload that records preset / benchmark / custom counts together
- `docs/artifacts/page-replacement-lab/trace-compare/mobile-app-session-vs-reporting-scan-session-trace-compare.{md,svg,csv,json,html}` — committed side-by-side imported-trace bundle that contrasts a locality-friendly mobile session against a scan-heavy reporting session
- `docs/artifacts/page-replacement-lab/wsclock-window/compiler-phase-shift-window1-study.{md,svg,csv,json}` — committed WSClock sensitivity bundle that shows how a tighter `tau` window changes the compiler benchmark study
- `projects/page-replacement-lab/custom-traces/mobile-app-session.txt` — sample imported trace file used to demonstrate custom aggregate, gallery, and trace-compare workflows without editing the source code
- `projects/page-replacement-lab/custom-traces/reporting-scan-session.txt` — sample imported trace file with repeated pinned hot pages separated by long cold scans for a stronger contrast workload

## Testing
```bash
python3 -m unittest discover -s projects/page-replacement-lab -p "test_*.py"
```

## Interview talking points
- explain why **OPT** is the gold-standard benchmark even though it is not implementable online
- describe how **Clock / second-chance** approximates recency using a reference bit and circular hand
- describe how **Aging** uses a shifting reference-bit history to approximate LRU with lower bookkeeping pressure than exact recency stacks
- explain how the simplified **WSClock** policy combines Clock hand scans with a virtual-time working-set window and an LRU-style fallback when every page still looks active
- explain how tightening or relaxing the WSClock `tau` / working-set window changes eviction aggressiveness on phase-shifted workloads
- explain why **LRU** and **OPT** are stack algorithms while **FIFO** is not
- walk through why FIFO can show Belady's anomaly and why Clock can still regress on some workloads even though it often behaves better in practice
- discuss how locality of reference changes the ranking between FIFO, Clock, Aging, WSClock, and LRU
- explain how reuse distance helps estimate locality pressure and why the trace-summary report flags scan-heavy phase changes
- compare two imported traces by normalized average fault rate and explain why the lower-rate winner still needs the frame-by-frame table for nuance
- suggest how this simulator could extend into dirty-page-aware WSClock replay, richer working-set analysis, or more narrative report/gallery generation

## Future improvements
- add dirty-page-aware WSClock scans or adaptive `tau` / working-set-window heuristics for deeper systems realism
- generate richer HTML gallery drill-down pages for custom traces or side-by-side policy narratives
- add narrative annotations or callout overlays that explain why one imported trace wins on specific frame counts

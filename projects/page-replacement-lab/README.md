# Page Replacement Lab

A virtual-memory simulator for comparing classic page replacement strategies on the same reference string, with built-in workload presets and frame-range studies that surface FIFO Belady anomalies and other fault regressions.

## Why this project matters
- demonstrates operating-systems and memory-management fundamentals in runnable code
- compares practical online heuristics against the theoretical optimal baseline
- includes **Clock / second-chance**, a more realistic policy than pure FIFO for systems interviews
- makes page-fault tradeoffs visible with deterministic step traces, reusable presets, and frame-range studies
- gives strong interview material around locality, stack algorithms, and Belady's anomaly
- leaves room for future extensions like trace-file replay, working-set sampling, or chart exports

## Features
- simulate **FIFO**, **Clock / second-chance**, **LRU**, and **OPT** page replacement
- load a reference string from repeated `--page` flags, a file, or a built-in preset
- print a step-by-step trace for one algorithm
- compare all four algorithms on the same workload
- run a frame-range study to detect FIFO Belady anomalies and other fault regressions
- list built-in workload presets for repeatable demos and screenshots
- export structured JSON for reports, demos, or frontend visualizations later
- export study results as Markdown, CSV, and self-contained SVG cards for README screenshots and portfolio pages
- generate a multi-workload HTML gallery that bundles inline SVG study cards with downloadable Markdown / SVG / CSV / JSON companions

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

### Compare FIFO / Clock / LRU / OPT
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py compare --frames 3 \
  --preset classic-belady
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

### Build a browsable gallery across all built-in workloads
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py gallery --min-frames 2 --max-frames 6 \
  --artifact-dir docs/artifacts/page-replacement-lab/gallery
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
Use either `--preset` or explicit `--page` / `--pages-file` input for a given run, not both.

## Example output
```text
frames: 3
source: preset classic-belady — classic Belady anomaly reference string that makes FIFO regress from 3 to 4 frames
reference: 1 2 3 4 1 2 5 1 2 3 4 5
algorithm  faults  hits  hit-rate
fifo       9       3      25.00%
clock      9       3      25.00%
lru        10      2      16.67%
opt        7       5      41.67%
best faults: 7 (opt)
```

## Committed artifact examples
- `docs/artifacts/page-replacement-lab/classic-belady-study.md` — narrative study report with the winner table and anomaly callouts
- `docs/artifacts/page-replacement-lab/classic-belady-study.svg` — screenshot-ready chart card for README or portfolio galleries
- `docs/artifacts/page-replacement-lab/classic-belady-study.csv` — spreadsheet/chart-friendly export of the same frame sweep
- `docs/artifacts/page-replacement-lab/gallery/index.html` — browsable multi-workload gallery with inline SVG charts and download links for each preset bundle
- `docs/artifacts/page-replacement-lab/gallery/*.json` — machine-readable study payloads for each built-in preset

## Testing
```bash
python3 -m unittest discover -s projects/page-replacement-lab -p "test_*.py"
```

## Interview talking points
- explain why **OPT** is the gold-standard benchmark even though it is not implementable online
- describe how **Clock / second-chance** approximates recency using a reference bit and circular hand
- explain why **LRU** and **OPT** are stack algorithms while **FIFO** is not
- walk through why FIFO can show Belady's anomaly and why Clock can still regress on some workloads even though it often behaves better in practice
- discuss how locality of reference changes the ranking between FIFO, Clock, and LRU
- suggest how this simulator could extend into real trace replay, working-set analysis, or richer report/gallery generation

## Future improvements
- import larger trace files for repeatable benchmark suites
- add working-set or aging-style algorithms for richer policy comparisons
- add cross-workload aggregate comparison charts that put several presets on the same axes
- generate richer HTML gallery drill-down pages for custom traces or side-by-side policy narratives

# Page Replacement Lab

A virtual-memory simulator for comparing classic page replacement strategies on the same reference string, with a built-in study mode for spotting FIFO Belady anomalies.

## Why this project matters
- demonstrates operating-systems and memory-management fundamentals in runnable code
- compares online heuristics against the theoretical optimal baseline
- makes page-fault tradeoffs visible with deterministic step traces and frame-range studies
- gives strong interview material around locality, stack algorithms, and Belady's anomaly
- leaves room for future extensions like Clock, working-set sampling, or trace-file benchmarks

## Features
- simulate **FIFO**, **LRU**, and **OPT** page replacement
- load a reference string from repeated `--page` flags or a file
- print a step-by-step trace for one algorithm
- compare all three algorithms on the same workload
- run a frame-range study to detect FIFO Belady anomalies
- export structured JSON for reports, demos, or frontend visualizations later

## Quick start

### Simulate one algorithm with a trace
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py simulate fifo --frames 3 \
  --page 1 --page 2 --page 3 --page 4 --page 1 --page 2 --page 5 --show-steps
```

### Compare FIFO / LRU / OPT
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py compare --frames 3 \
  --page 1 --page 2 --page 3 --page 4 --page 1 --page 2 --page 5 --page 1 --page 2 --page 3 --page 4 --page 5
```

### Study frame counts and flag FIFO anomalies
```bash
python3 projects/page-replacement-lab/page_replacement_lab.py study --min-frames 2 --max-frames 5 \
  --page 1 --page 2 --page 3 --page 4 --page 1 --page 2 --page 5 --page 1 --page 2 --page 3 --page 4 --page 5
```

## Example output
```text
frames: 3
reference: 1 2 3 4 1 2 5 1 2 3 4 5
algorithm  faults  hits  hit-rate
fifo      9       3      25.00%
lru       10      2      16.67%
opt       7       5      41.67%
```

## Testing
```bash
python3 -m unittest discover -s projects/page-replacement-lab -p "test_*.py"
```

## Interview talking points
- explain why **OPT** is the gold-standard benchmark even though it is not implementable online
- describe why **LRU** avoids Belady's anomaly while **FIFO** can regress when frames increase
- walk through how locality of reference changes the ranking between FIFO and LRU
- discuss how this simulator could extend into real trace replay or working-set analysis

## Future improvements
- add Clock / second-chance replacement for a more realistic systems tradeoff
- import larger trace files for repeatable benchmark suites
- export charts that show page faults vs. frame count across multiple workloads
- add workload presets for sequential scans, looping hot sets, and mixed locality bursts

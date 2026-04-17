# branch-predictor-lab

A compact computer-architecture portfolio project for simulating classic branch predictors against local branch traces or reproducible synthetic workloads.

## Why this project is worth showing
- demonstrates core CPU architecture ideas beyond the usual data-structures portfolio set
- compares naive baselines with realistic stateful predictors students see in computer architecture courses
- stays practical: trace parsing, configurable tables, synthetic workload generation, JSON output, and tests make it easy to demo or extend

## Implemented predictors
- `always-taken`
- `always-not-taken`
- `one-bit` bimodal table
- `two-bit` saturating-counter bimodal table
- `local-history` two-level predictor with per-PC history registers
- `gshare` with XOR-based global history
- `tournament` chooser that combines local-history and gshare

## Implemented synthetic workloads
- `loop-heavy` — repeated loop backedges with explicit exits so one-bit vs two-bit behavior is easy to show
- `random-biased` — several static branches with different taken probabilities for reproducible baseline sweeps
- `tournament-style` — a mixed trace that combines correlated-history branches, loop behavior, and biased cleanup branches to motivate hybrid predictors

## Trace format
Use one branch per line:

```text
<address> <outcome> [optional-target] [optional-label]
```

Examples:

```text
0x100 T
0x100 N 0x104 loop-exit
0x204 T 0x260 cache-hit
```

Accepted outcomes: `T`, `N`, `taken`, `not-taken`, `1`, `0`, `true`, `false`.
Comments starting with `#` are ignored.

## Quick start

Compare predictors on the bundled sample trace:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py compare \
  projects/branch-predictor-lab/sample_trace.txt \
  --table-size 16 \
  --history-bits 2
```

Generate a synthetic workload and inspect it as JSON:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py generate \
  tournament-style \
  --branches 16 \
  --seed 3 \
  --json
```

Write a loop-focused trace to disk for later experiments:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py generate \
  loop-heavy \
  --branches 20 \
  --output /tmp/loop-heavy.trace
```

Example comparison output:

```text
predictor          accuracy   mispreds   mpki    hardest branch
----------------  ---------  ---------  ------  ---------------
local-history       75.00%          6   250.0  0x100
tournament          75.00%          6   250.0  0x100
gshare              70.83%          7   291.7  0x100
always-taken        62.50%          9   375.0  0x140
two-bit             62.50%          9   375.0  0x140
always-not-taken    37.50%         15   625.0  0x100
one-bit             25.00%         18   750.0  0x140
```

## Useful commands

Run the full comparison suite on the bundled trace:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py compare \
  projects/branch-predictor-lab/sample_trace.txt --json
```

Inspect one specific predictor:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py simulate \
  projects/branch-predictor-lab/sample_trace.txt \
  --predictor tournament \
  --history-bits 2 \
  --json
```

Create a reproducible random-bias trace and compare it right away:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py generate \
  random-biased \
  --branches 48 \
  --seed 11 \
  --output /tmp/random-biased.trace
python3 projects/branch-predictor-lab/branch_predictor.py compare \
  /tmp/random-biased.trace \
  --table-size 16 \
  --history-bits 2
```

For the mixed tournament-style trace, use a deeper history length so gshare can exploit the correlated branch pair:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py generate \
  tournament-style \
  --branches 48 \
  --seed 5 \
  --output /tmp/tournament-style.trace
python3 projects/branch-predictor-lab/branch_predictor.py compare \
  /tmp/tournament-style.trace \
  --table-size 16 \
  --history-bits 4
```

Run the tests:

```bash
.venv/bin/pytest tests/test_branch_predictor_lab.py
```

## Design notes
- branch tables are indexed with `(pc >> 2)` so aligned instruction addresses collapse the low two zero bits
- the one-bit predictor flips immediately after a miss, which makes loop-exit behavior easy to understand but noisy on phase changes
- the two-bit predictor uses the standard 2-bit saturating states (`00`, `01`, `10`, `11`) and defaults to weakly taken
- the local-history predictor keeps a short per-PC history register and uses that pattern to pick a saturating counter, which makes repeated branch-local motifs easy to demonstrate
- gshare keeps a small global history register and XORs it with the branch address bits so one static branch can map to different counters based on recent behavior
- the tournament predictor tracks when local-history vs gshare is doing better for a given PC and exposes chooser-state snapshots so the hybrid behavior is inspectable in JSON output
- the synthetic generator is intentionally lightweight and reproducible so you can build demos, tests, and benchmark sweeps without needing a large external trace corpus

## Portfolio talking points
- explain why one-bit predictors mispredict both loop exit and loop re-entry while two-bit predictors usually miss only on the exit
- use the `tournament-style` workload to show why some branches want local-history tracking while others benefit from recent-history correlation
- compare `local-history`, `gshare`, and `tournament` on the same trace to talk through hybrid prediction instead of stopping at bimodal counters
- show recruiters or classmates that the project can generate its own controlled traces, which makes your benchmarking story stronger than a single hand-written input file
- extend the simulator with perceptron prediction if you want a stronger architecture capstone story

## Future improvements
- render Markdown/SVG predictor comparison cards for the docs artifact gallery
- add a perceptron predictor follow-up for advanced architecture coverage
- add trace-family sweep commands that run multiple generated workloads in one shot

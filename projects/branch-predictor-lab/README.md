# branch-predictor-lab

A compact computer-architecture portfolio project for simulating classic branch predictors against a local branch trace.

## Why this project is worth showing
- demonstrates core CPU architecture ideas beyond the usual data-structures portfolio set
- compares naive baselines with realistic stateful predictors students see in computer architecture courses
- stays practical: trace parsing, configurable tables, JSON output, and tests make it easy to demo or extend

## Implemented predictors
- `always-taken`
- `always-not-taken`
- `one-bit` bimodal table
- `two-bit` saturating-counter bimodal table
- `gshare` with XOR-based global history

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

```bash
python3 projects/branch-predictor-lab/branch_predictor.py compare \
  projects/branch-predictor-lab/sample_trace.txt \
  --table-size 16 \
  --history-bits 2
```

Example text output:

```text
predictor          accuracy   mispreds   mpki    hardest branch
----------------  ---------  ---------  ------  ---------------
gshare              70.83%          7   291.7  0x100
always-taken        62.50%          9   375.0  0x140
two-bit             62.50%          9   375.0  0x140
always-not-taken    37.50%         15   625.0  0x100
one-bit             25.00%         18   750.0  0x140
```

## Useful commands

Run the full comparison suite:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py compare \
  projects/branch-predictor-lab/sample_trace.txt --json
```

Inspect one specific predictor:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py simulate \
  projects/branch-predictor-lab/sample_trace.txt \
  --predictor gshare \
  --history-bits 2 \
  --json
```

Run the tests:

```bash
.venv/bin/pytest tests/test_branch_predictor_lab.py
```

## Design notes
- branch tables are indexed with `(pc >> 2)` so aligned instruction addresses collapse the low two zero bits
- the one-bit predictor flips immediately after a miss, which makes loop-exit behavior easy to understand but noisy on phase changes
- the two-bit predictor uses the standard 2-bit saturating states (`00`, `01`, `10`, `11`) and defaults to weakly taken
- gshare keeps a small global history register and XORs it with the branch address bits so one static branch can map to different counters based on recent behavior

## Portfolio talking points
- explain why one-bit predictors mispredict both loop exit and loop re-entry while two-bit predictors usually miss only on the exit
- use the alternating branch in `sample_trace.txt` to show where global history helps more than pure per-address bias
- extend the simulator with tournament or perceptron prediction if you want a stronger architecture capstone story

## Future improvements
- add synthetic trace generators for controlled accuracy sweeps
- export Markdown/SVG scorecards for easy README screenshots
- add tournament or perceptron predictors and compare training cost vs accuracy

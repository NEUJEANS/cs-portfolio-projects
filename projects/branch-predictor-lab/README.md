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
- `perceptron` neural predictor with signed global-history weights
- `tournament` chooser that combines local-history and gshare

## Implemented synthetic workloads
- `loop-heavy` — repeated loop backedges with explicit exits so one-bit vs two-bit behavior is easy to show
- `random-biased` — several static branches with different taken probabilities for reproducible baseline sweeps
- `tournament-style` — a mixed trace that combines correlated-history branches, loop behavior, and biased cleanup branches to motivate hybrid predictors
- `alias-thrash` — paired static PCs deliberately collide in the same small predictor-table buckets with opposite taken biases so aliasing is visible in reports
- `perceptron-majority` — a linearly separable long-history trace designed to show why perceptrons can generalize beyond small saturating-counter tables

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

Generate one overview artifact that compares all built-in synthetic workload families with their recommended configs:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py sweep \
  --trace-dir artifacts/branch-predictor-lab/sweep \
  --markdown-out docs/artifacts/branch-predictor-lab/trace-family-sweep.md \
  --svg-out docs/artifacts/branch-predictor-lab/trace-family-sweep.svg
```

Generate a budget-normalized artifact that lets predictors compete under roughly equal state-bit budgets instead of one shared table/history setting:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep \
  --trace-dir artifacts/branch-predictor-lab/budget-sweep \
  --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md \
  --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg
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

Inspect a tuned perceptron run with explicit confidence/clamp settings:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py simulate \
  artifacts/branch-predictor-lab/perceptron-majority-seed13.trace \
  --predictor perceptron \
  --table-size 32 \
  --history-bits 12 \
  --threshold 19 \
  --weight-limit 74 \
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

Generate an alias-heavy trace to show how small tables force unrelated PCs to share the same predictor entries:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py generate \
  alias-thrash \
  --branches 48 \
  --seed 7 \
  --output /tmp/alias-thrash.trace
python3 projects/branch-predictor-lab/branch_predictor.py compare \
  /tmp/alias-thrash.trace \
  --table-size 16 \
  --history-bits 4 \
  --json
```

Generate a long-history workload that gives the perceptron predictor a fair demo case:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py generate \
  perceptron-majority \
  --branches 96 \
  --seed 13 \
  --output /tmp/perceptron-majority.trace
python3 projects/branch-predictor-lab/branch_predictor.py compare \
  /tmp/perceptron-majority.trace \
  --table-size 32 \
  --history-bits 12 \
  --json
```

To reproduce the committed gallery artifact for this slice, use the seeded trace and committed docs paths:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py generate \
  perceptron-majority \
  --branches 96 \
  --seed 13 \
  --output artifacts/branch-predictor-lab/perceptron-majority-seed13.trace
python3 projects/branch-predictor-lab/branch_predictor.py compare \
  artifacts/branch-predictor-lab/perceptron-majority-seed13.trace \
  --table-size 32 \
  --history-bits 12 \
  --markdown-out docs/artifacts/branch-predictor-lab/perceptron-majority-comparison.md \
  --svg-out docs/artifacts/branch-predictor-lab/perceptron-majority-comparison.svg \
  --json
```

To reproduce the committed trace-family sweep overview artifact, run the batch command with the committed output paths:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py sweep \
  --trace-dir artifacts/branch-predictor-lab/sweep \
  --markdown-out docs/artifacts/branch-predictor-lab/trace-family-sweep.md \
  --svg-out docs/artifacts/branch-predictor-lab/trace-family-sweep.svg \
  --json
```

To reproduce the committed perceptron tuning artifact, sweep the seeded long-history trace with the committed threshold/weight grid:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py perceptron-sweep \
  artifacts/branch-predictor-lab/perceptron-majority-seed13.trace \
  --table-size 32 \
  --history-bits 12 \
  --thresholds 19 28 37 46 55 \
  --weight-limits 18 37 74 148 \
  --markdown-out docs/artifacts/branch-predictor-lab/perceptron-tuning-sweep.md \
  --svg-out docs/artifacts/branch-predictor-lab/perceptron-tuning-sweep.svg \
  --json
```

To reproduce the committed budget-normalized sweep artifact, search the committed state-bit grid and write the matching report/card pair:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep \
  --trace-dir artifacts/branch-predictor-lab/budget-sweep \
  --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md \
  --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg \
  --json
```

Export recruiter-friendly Markdown and SVG comparison cards from the same compare command:

```bash
python3 projects/branch-predictor-lab/branch_predictor.py compare \
  projects/branch-predictor-lab/sample_trace.txt \
  --table-size 16 \
  --history-bits 2 \
  --markdown-out docs/artifacts/branch-predictor-lab/sample-trace-comparison.md \
  --svg-out docs/artifacts/branch-predictor-lab/sample-trace-comparison.svg
```

See the committed gallery at [`docs/artifacts/branch-predictor-lab/index.md`](../../docs/artifacts/branch-predictor-lab/index.md).

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
- the perceptron predictor keeps a signed weight vector per static branch bucket and trains it with the classic update rule when the prediction is wrong or not confident, which makes long-history correlations explainable instead of purely table-lookup based
- the `perceptron-sweep` command turns threshold and weight-clamp tuning into a committed Markdown/SVG artifact, so the neural predictor story includes practical parameter sensitivity instead of only one lucky run
- the `budget-sweep` command searches best-fit configs under shared approximate state-bit budgets and can now emit a CSV winner matrix, which makes it easier to explain why a “best” predictor can change once hardware cost is constrained and to reuse the matrix in charts without scraping Markdown
- the tournament predictor tracks when local-history vs gshare is doing better for a given PC and exposes chooser-state snapshots so the hybrid behavior is inspectable in JSON output
- compare output includes both a static PC-index aliasing summary and a dynamic gshare-index aliasing summary, so you can point at exact colliding buckets and history-conditioned conflicts when discussing table-size trade-offs
- the `alias-thrash` generator intentionally maps opposite-bias branches into the same low-order index bits, which makes interference easy to show without external trace corpora
- the synthetic generator is intentionally lightweight and reproducible so you can build demos, tests, and benchmark sweeps without needing a large external trace corpus
- the `sweep` command uses per-workload recommended table/history settings so one overview artifact can stay fair to loop, bias, aliasing, hybrid, and perceptron-friendly traces instead of flattening everything into one generic config

## Portfolio talking points
- explain why one-bit predictors mispredict both loop exit and loop re-entry while two-bit predictors usually miss only on the exit
- use the `tournament-style` workload to show why some branches want local-history tracking while others benefit from recent-history correlation
- use the `alias-thrash` workload plus the compare JSON/Markdown static + dynamic alias summaries to explain predictor-table interference, gshare history-conditioned collisions, and why larger tables can recover accuracy
- compare `local-history`, `gshare`, `perceptron`, and `tournament` on the same trace to talk through local/global/neural/hybrid trade-offs instead of stopping at bimodal counters
- use the `perceptron-majority` workload to explain linearly separable branch behavior and why perceptrons can use longer histories without exploding the table size
- use the perceptron tuning sweep when you want to show that confidence thresholds and hardware-friendly weight clamps still shape the final accuracy story
- use the trace-family sweep card when you want one overview slide that shows different workloads favor different predictors instead of implying there is one universal winner
- show recruiters or classmates that the project can generate its own controlled traces, which makes your benchmarking story stronger than a single hand-written input file

## Future improvements
- add side-by-side table-size sweep artifacts so static-PC and dynamic-gshare collision counts can be compared across the same workload family
- add artifact-ready stacked bar / heatmap exports that summarize how often each predictor wins across the whole budget grid, not just per-workload rows

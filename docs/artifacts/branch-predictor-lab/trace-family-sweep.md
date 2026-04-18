# Branch predictor trace-family sweep

- Generated: `2026-04-18T03:03:11Z`
- Workloads: `5` synthetic families run in one batch command
- Goal: show how the recommended trace/config pairs shift the best predictor across loop, bias, aliasing, mixed-history, and perceptron-friendly cases.

## Overview

| Workload | Focus | Branches | Table | History | Best | Accuracy | Runner-up | Gap |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- | ---: |
| `loop-heavy` | loop backedges and exits | `40` | `8` | `4` | `local-history` | `82.50%` | `tournament` | `0.00 pp` |
| `random-biased` | biased hot/cold guard branches | `96` | `16` | `2` | `always-taken` | `52.08%` | `one-bit` | `1.04 pp` |
| `tournament-style` | mixed local/global correlation | `48` | `16` | `4` | `perceptron` | `77.08%` | `gshare` | `4.17 pp` |
| `alias-thrash` | small-table alias interference | `64` | `16` | `4` | `perceptron` | `79.69%` | `local-history` | `4.69 pp` |
| `perceptron-majority` | long-history linearly separable branch | `96` | `32` | `12` | `perceptron` | `92.71%` | `local-history` | `4.17 pp` |

## Per-workload notes

### `loop-heavy`

- Focus: loop backedges and exits
- Config: `branches=40` · `seed=7` · `table=8` · `history=4`
- Winner: `local-history` at `82.50%` with `7` mispredictions.
- Best simple baseline: `always-taken` at `80.00%`.
- Best advanced predictor: `local-history` at `82.50%`.
- Static aliasing: `1` colliding buckets, `0` with conflicting dominant biases.
- Dynamic gshare aliasing: `4` live collisions, `1` with conflicting dominant biases, `2` spanning multiple history states.

Top three predictors:
- `local-history` · `82.50%` accuracy · `7` mispredictions
- `tournament` · `82.50%` accuracy · `7` mispredictions
- `always-taken` · `80.00%` accuracy · `8` mispredictions

### `random-biased`

- Focus: biased hot/cold guard branches
- Config: `branches=96` · `seed=11` · `table=16` · `history=2`
- Winner: `always-taken` at `52.08%` with `46` mispredictions.
- Best simple baseline: `always-taken` at `52.08%`.
- Best advanced predictor: `perceptron` at `46.88%`.
- Static aliasing: `1` colliding buckets, `1` with conflicting dominant biases.
- Dynamic gshare aliasing: `4` live collisions, `4` with conflicting dominant biases, `0` spanning multiple history states.

Top three predictors:
- `always-taken` · `52.08%` accuracy · `46` mispredictions
- `one-bit` · `51.04%` accuracy · `47` mispredictions
- `always-not-taken` · `47.92%` accuracy · `50` mispredictions

### `tournament-style`

- Focus: mixed local/global correlation
- Config: `branches=48` · `seed=5` · `table=16` · `history=4`
- Winner: `perceptron` at `77.08%` with `11` mispredictions.
- Best simple baseline: `one-bit` at `68.75%`.
- Best advanced predictor: `perceptron` at `77.08%`.
- Static aliasing: `1` colliding buckets, `1` with conflicting dominant biases.
- Dynamic gshare aliasing: `8` live collisions, `4` with conflicting dominant biases, `0` spanning multiple history states.

Top three predictors:
- `perceptron` · `77.08%` accuracy · `11` mispredictions
- `gshare` · `72.92%` accuracy · `13` mispredictions
- `local-history` · `72.92%` accuracy · `13` mispredictions

### `alias-thrash`

- Focus: small-table alias interference
- Config: `branches=64` · `seed=7` · `table=16` · `history=4`
- Winner: `perceptron` at `79.69%` with `13` mispredictions.
- Best simple baseline: `always-taken` at `54.69%`.
- Best advanced predictor: `perceptron` at `79.69%`.
- Static aliasing: `2` colliding buckets, `2` with conflicting dominant biases.
- Dynamic gshare aliasing: `10` live collisions, `3` with conflicting dominant biases, `8` spanning multiple history states.

Top three predictors:
- `perceptron` · `79.69%` accuracy · `13` mispredictions
- `local-history` · `75.00%` accuracy · `16` mispredictions
- `gshare` · `73.44%` accuracy · `17` mispredictions

### `perceptron-majority`

- Focus: long-history linearly separable branch
- Config: `branches=96` · `seed=13` · `table=32` · `history=12`
- Winner: `perceptron` at `92.71%` with `7` mispredictions.
- Best simple baseline: `always-not-taken` at `75.00%`.
- Best advanced predictor: `perceptron` at `92.71%`.
- Static aliasing: `0` colliding buckets, `0` with conflicting dominant biases.
- Dynamic gshare aliasing: `5` live collisions, `2` with conflicting dominant biases, `5` spanning multiple history states.

Top three predictors:
- `perceptron` · `92.71%` accuracy · `7` mispredictions
- `local-history` · `88.54%` accuracy · `11` mispredictions
- `tournament` · `87.50%` accuracy · `12` mispredictions

## Portfolio usage

- Use this sweep report when you want one artifact that compares multiple branch families without manually running five separate `generate` + `compare` commands.
- Pair the sweep SVG with the existing per-trace cards when you need both an overview slide and deeper single-trace evidence.
- The report is intentionally configuration-aware so interviewers can see that long-history perceptron cases use deeper history than simple bias/loop demos.

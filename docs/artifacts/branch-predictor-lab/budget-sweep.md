# Branch predictor budget-normalized sweep

- Generated: `2026-04-18T08:45:53Z`
- Workloads: `5` synthetic families
- Compared budgets: `64 bits, 128 bits, 256 bits, 512 bits, 1024 bits`
- Search space: table sizes `4, 8, 16, 32, 64` · history bits `1, 2, 4, 8, 12` · perceptron weight limits `15, 31, 74`
- Goal: compare the best config each predictor can afford under the same approximate state-bit budget instead of one fixed table/history setting for everyone.
- Export note: the SVG now includes whole-grid win totals, a budget-by-predictor heatmap, a winner-margin trend card, a crossover card, and blue flip chips on the winner matrix cells that mark exactly where the winning predictor changes.

## Overview

| Workload | `64 bits` | `128 bits` | `256 bits` | `512 bits` | `1024 bits` |
| --- | --- | --- | --- | --- | --- |
| `loop-heavy` | `gshare` 82.50% | `gshare` 87.50% | `gshare` 90.00% | `gshare` 90.00% | `gshare` 90.00% |
| `random-biased` | `always-taken` 52.08% | `two-bit` 63.54% | `two-bit` 63.54% | `two-bit` 63.54% | `two-bit` 63.54% |
| `tournament-style` | `gshare` 72.92% | `gshare` 77.08% | `gshare` 77.08% | `tournament` 83.33% | `tournament` 83.33% |
| `alias-thrash` | `local-history` 79.69% | `gshare` 81.25% | `gshare` 81.25% | `gshare` 81.25% | `gshare` 81.25% |
| `perceptron-majority` | `perceptron` 82.29% | `perceptron` 82.29% | `gshare` 83.33% | `perceptron` 92.71% | `perceptron` 92.71% |

## Whole-grid winner summary

- Grid cells: `25` workload-budget combinations.
- Overall leader: `gshare` with `13` wins (`52.00%` of the grid).

| Predictor | Grid wins | Share | Workloads won | Budgets won |
| --- | ---: | ---: | ---: | --- |
| `gshare` | `13` | `52.00%` | `4` | `64, 128, 256, 512, 1024` |
| `two-bit` | `4` | `16.00%` | `1` | `128, 256, 512, 1024` |
| `perceptron` | `4` | `16.00%` | `1` | `64, 128, 512, 1024` |
| `tournament` | `2` | `8.00%` | `1` | `512, 1024` |
| `always-taken` | `1` | `4.00%` | `1` | `64` |
| `local-history` | `1` | `4.00%` | `1` | `64` |

### Budget × predictor win counts

| Predictor | `64 bits` | `128 bits` | `256 bits` | `512 bits` | `1024 bits` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `gshare` | `2` | `3` | `4` | `2` | `2` |
| `two-bit` | `0` | `1` | `1` | `1` | `1` |
| `perceptron` | `1` | `1` | `0` | `1` | `1` |
| `tournament` | `0` | `0` | `0` | `1` | `1` |
| `always-taken` | `1` | `0` | `0` | `0` | `0` |
| `local-history` | `1` | `0` | `0` | `0` | `0` |

## Winner crossover points

- Exact winner flips: `5` across `4` workloads.

### Transition counts

| Budget step | Winner flip | Count | Workloads |
| --- | --- | ---: | --- |
| `64→128 bits` | `always-taken → two-bit` | `1` | `random-biased` |
| `64→128 bits` | `local-history → gshare` | `1` | `alias-thrash` |
| `128→256 bits` | `perceptron → gshare` | `1` | `perceptron-majority` |
| `256→512 bits` | `gshare → perceptron` | `1` | `perceptron-majority` |
| `256→512 bits` | `gshare → tournament` | `1` | `tournament-style` |

### Workload crossover triggers

| Workload | Trigger budget step | Winner flip | Before gap | After gap |
| --- | --- | --- | ---: | ---: |
| `alias-thrash` | `64→128 bits` | `local-history → gshare` | `0.00 pp` | `1.56 pp` |
| `random-biased` | `64→128 bits` | `always-taken → two-bit` | `0.00 pp` | `10.42 pp` |
| `perceptron-majority` | `128→256 bits` | `perceptron → gshare` | `1.04 pp` | `1.04 pp` |
| `perceptron-majority` | `256→512 bits` | `gshare → perceptron` | `1.04 pp` | `9.38 pp` |
| `tournament-style` | `256→512 bits` | `gshare → tournament` | `0.00 pp` | `6.25 pp` |

## Margin and runner-up story

- Photo finishes (≤0.50 pp): `9` grid cells (`36.00%`).
- Close races (≤1.00 pp): `9` grid cells (`36.00%`).
- Tightest cell: `loop-heavy` @ `64 bits` → `gshare` over `local-history` by `0.00 pp`.
- Widest cell: `random-biased` @ `128 bits` → `two-bit` over `gshare` by `10.42 pp`.

### Margin trend by budget

| Budget | Avg winner gap | Photo finishes (≤0.50 pp) | Close races (≤1.00 pp) | Most common runner-up |
| ---: | ---: | ---: | ---: | --- |
| `64` | `0.21 pp` | `4` | `4` | `local-history` (`2/5` cells) |
| `128` | `3.60 pp` | `1` | `1` | `local-history` (`3/5` cells) |
| `256` | `2.65 pp` | `1` | `1` | `local-history` (`3/5` cells) |
| `512` | `4.75 pp` | `1` | `1` | `gshare` (`3/5` cells) |
| `1024` | `2.25 pp` | `2` | `2` | `perceptron` (`3/5` cells) |

### Runner-up stability by workload

| Workload | Runner-up flow | Changes | Tightest gap | Widest gap |
| --- | --- | ---: | --- | --- |
| `loop-heavy` | `local-history ×3 → tournament ×2` | `1` | `64 bits` (`0.00 pp`) | `256 bits` (`7.50 pp`) |
| `random-biased` | `two-bit → gshare ×3 → perceptron` | `2` | `64 bits` (`0.00 pp`) | `128 bits` (`10.42 pp`) |
| `tournament-style` | `local-history ×3 → gshare → perceptron` | `2` | `64 bits` (`0.00 pp`) | `512 bits` (`6.25 pp`) |
| `alias-thrash` | `perceptron → local-history ×2 → perceptron ×2` | `2` | `64 bits` (`0.00 pp`) | `128 bits` (`1.56 pp`) |
| `perceptron-majority` | `gshare ×2 → perceptron → gshare → tournament` | `3` | `1024 bits` (`0.00 pp`) | `512 bits` (`9.38 pp`) |

## Per-workload notes

### `loop-heavy`

- Focus: loop backedges and exits
- Trace config: `branches=40` · `seed=7`
- Winner sequence: 64b:gshare → 128b:gshare → 256b:gshare → 512b:gshare → 1024b:gshare
- Crossover points: none
- SVG matrix callouts: none

| Budget | Winner | Runner-up | Matrix callout | Best simple | Best advanced |
| ---: | --- | --- | --- | --- | --- |
| `64` | `gshare` `82.50%` | `local-history` (`0.00 pp` gap) | - | `always-taken` `80.00%` | `gshare` `82.50%` |
| `128` | `gshare` `87.50%` | `local-history` (`5.00 pp` gap) | - | `always-taken` `80.00%` | `gshare` `87.50%` |
| `256` | `gshare` `90.00%` | `local-history` (`7.50 pp` gap) | - | `always-taken` `80.00%` | `gshare` `90.00%` |
| `512` | `gshare` `90.00%` | `tournament` (`5.00 pp` gap) | - | `always-taken` `80.00%` | `gshare` `90.00%` |
| `1024` | `gshare` `90.00%` | `tournament` (`5.00 pp` gap) | - | `always-taken` `80.00%` | `gshare` `90.00%` |

Representative best-fit configs:
- `64 bits` → gshare 82.50% (gshare · table=16 · history=4 · bits=36); local-history 82.50% (local-history · table=4 · history=4 · bits=48); always-taken 80.00% (always-taken · stateless)
- `128 bits` → gshare 87.50% (gshare · table=32 · history=4 · bits=68); local-history 82.50% (local-history · table=4 · history=4 · bits=48); tournament 82.50% (tournament · table=8 · history=4 · bits=100)
- `256 bits` → gshare 90.00% (gshare · table=64 · history=4 · bits=132); local-history 82.50% (local-history · table=4 · history=4 · bits=48); tournament 82.50% (tournament · table=8 · history=4 · bits=100)
- `512 bits` → gshare 90.00% (gshare · table=64 · history=4 · bits=132); tournament 85.00% (tournament · table=32 · history=4 · bits=292); local-history 82.50% (local-history · table=4 · history=4 · bits=48)
- `1024 bits` → gshare 90.00% (gshare · table=64 · history=4 · bits=132); tournament 85.00% (tournament · table=32 · history=4 · bits=292); local-history 85.00% (local-history · table=32 · history=8 · bits=768)

### `random-biased`

- Focus: biased hot/cold guard branches
- Trace config: `branches=96` · `seed=11`
- Winner sequence: 64b:always-taken → 128b:two-bit → 256b:two-bit → 512b:two-bit → 1024b:two-bit
- Crossover points: 64→128b always-taken→two-bit
- SVG matrix callouts: 64→128b marks always-taken → two-bit

| Budget | Winner | Runner-up | Matrix callout | Best simple | Best advanced |
| ---: | --- | --- | --- | --- | --- |
| `64` | `always-taken` `52.08%` | `two-bit` (`0.00 pp` gap) | - | `always-taken` `52.08%` | `local-history` `51.04%` |
| `128` | `two-bit` `63.54%` | `gshare` (`10.42 pp` gap) | `64→128b` `always-taken → two-bit` | `two-bit` `63.54%` | `gshare` `53.12%` |
| `256` | `two-bit` `63.54%` | `gshare` (`3.12 pp` gap) | - | `two-bit` `63.54%` | `gshare` `60.42%` |
| `512` | `two-bit` `63.54%` | `gshare` (`3.12 pp` gap) | - | `two-bit` `63.54%` | `gshare` `60.42%` |
| `1024` | `two-bit` `63.54%` | `perceptron` (`2.08 pp` gap) | - | `two-bit` `63.54%` | `perceptron` `61.46%` |

Representative best-fit configs:
- `64 bits` → always-taken 52.08% (always-taken · stateless); two-bit 52.08% (two-bit · table=32 · bits=64); one-bit 52.08% (one-bit · table=64 · bits=64)
- `128 bits` → two-bit 63.54% (two-bit · table=64 · bits=128); gshare 53.12% (gshare · table=32 · history=4 · bits=68); always-taken 52.08% (always-taken · stateless)
- `256 bits` → two-bit 63.54% (two-bit · table=64 · bits=128); gshare 60.42% (gshare · table=64 · history=1 · bits=129); local-history 56.25% (local-history · table=32 · history=4 · bits=160)
- `512 bits` → two-bit 63.54% (two-bit · table=64 · bits=128); gshare 60.42% (gshare · table=64 · history=1 · bits=129); tournament 60.42% (tournament · table=32 · history=4 · bits=292)
- `1024 bits` → two-bit 63.54% (two-bit · table=64 · bits=128); perceptron 61.46% (perceptron · table=64 · history=1 · w=15 · bits=641); gshare 60.42% (gshare · table=64 · history=1 · bits=129)

### `tournament-style`

- Focus: mixed local/global correlation
- Trace config: `branches=48` · `seed=5`
- Winner sequence: 64b:gshare → 128b:gshare → 256b:gshare → 512b:tournament → 1024b:tournament
- Crossover points: 256→512b gshare→tournament
- SVG matrix callouts: 256→512b marks gshare → tournament

| Budget | Winner | Runner-up | Matrix callout | Best simple | Best advanced |
| ---: | --- | --- | --- | --- | --- |
| `64` | `gshare` `72.92%` | `local-history` (`0.00 pp` gap) | - | `one-bit` `68.75%` | `gshare` `72.92%` |
| `128` | `gshare` `77.08%` | `local-history` (`0.00 pp` gap) | - | `one-bit` `68.75%` | `gshare` `77.08%` |
| `256` | `gshare` `77.08%` | `local-history` (`0.00 pp` gap) | - | `one-bit` `68.75%` | `gshare` `77.08%` |
| `512` | `tournament` `83.33%` | `gshare` (`6.25 pp` gap) | `256→512b` `gshare → tournament` | `one-bit` `68.75%` | `tournament` `83.33%` |
| `1024` | `tournament` `83.33%` | `perceptron` (`4.17 pp` gap) | - | `one-bit` `68.75%` | `tournament` `83.33%` |

Representative best-fit configs:
- `64 bits` → gshare 72.92% (gshare · table=16 · history=4 · bits=36); local-history 72.92% (local-history · table=4 · history=4 · bits=48); one-bit 68.75% (one-bit · table=4 · bits=4)
- `128 bits` → gshare 77.08% (gshare · table=32 · history=4 · bits=68); local-history 77.08% (local-history · table=32 · history=2 · bits=72); perceptron 77.08% (perceptron · table=4 · history=4 · w=15 · bits=104)
- `256 bits` → gshare 77.08% (gshare · table=32 · history=4 · bits=68); local-history 77.08% (local-history · table=32 · history=2 · bits=72); perceptron 77.08% (perceptron · table=4 · history=4 · w=15 · bits=104)
- `512 bits` → tournament 83.33% (tournament · table=32 · history=4 · bits=292); gshare 77.08% (gshare · table=32 · history=4 · bits=68); local-history 77.08% (local-history · table=32 · history=2 · bits=72)
- `1024 bits` → tournament 83.33% (tournament · table=32 · history=4 · bits=292); perceptron 79.17% (perceptron · table=32 · history=4 · w=15 · bits=804); gshare 77.08% (gshare · table=32 · history=4 · bits=68)

### `alias-thrash`

- Focus: small-table alias interference
- Trace config: `branches=64` · `seed=7`
- Winner sequence: 64b:local-history → 128b:gshare → 256b:gshare → 512b:gshare → 1024b:gshare
- Crossover points: 64→128b local-history→gshare
- SVG matrix callouts: 64→128b marks local-history → gshare

| Budget | Winner | Runner-up | Matrix callout | Best simple | Best advanced |
| ---: | --- | --- | --- | --- | --- |
| `64` | `local-history` `79.69%` | `perceptron` (`0.00 pp` gap) | - | `two-bit` `79.69%` | `local-history` `79.69%` |
| `128` | `gshare` `81.25%` | `local-history` (`1.56 pp` gap) | `64→128b` `local-history → gshare` | `two-bit` `79.69%` | `gshare` `81.25%` |
| `256` | `gshare` `81.25%` | `local-history` (`1.56 pp` gap) | - | `two-bit` `79.69%` | `gshare` `81.25%` |
| `512` | `gshare` `81.25%` | `perceptron` (`0.00 pp` gap) | - | `two-bit` `79.69%` | `gshare` `81.25%` |
| `1024` | `gshare` `81.25%` | `perceptron` (`0.00 pp` gap) | - | `two-bit` `79.69%` | `gshare` `81.25%` |

Representative best-fit configs:
- `64 bits` → local-history 79.69% (local-history · table=4 · history=4 · bits=48); perceptron 79.69% (perceptron · table=4 · history=2 · w=15 · bits=62); two-bit 79.69% (two-bit · table=32 · bits=64)
- `128 bits` → gshare 81.25% (gshare · table=32 · history=1 · bits=65); local-history 79.69% (local-history · table=4 · history=4 · bits=48); perceptron 79.69% (perceptron · table=4 · history=2 · w=15 · bits=62)
- `256 bits` → gshare 81.25% (gshare · table=32 · history=1 · bits=65); local-history 79.69% (local-history · table=4 · history=4 · bits=48); perceptron 79.69% (perceptron · table=4 · history=2 · w=15 · bits=62)
- `512 bits` → gshare 81.25% (gshare · table=32 · history=1 · bits=65); perceptron 81.25% (perceptron · table=4 · history=12 · w=15 · bits=272); local-history 79.69% (local-history · table=4 · history=4 · bits=48)
- `1024 bits` → gshare 81.25% (gshare · table=32 · history=1 · bits=65); perceptron 81.25% (perceptron · table=4 · history=12 · w=15 · bits=272); local-history 79.69% (local-history · table=4 · history=4 · bits=48)

### `perceptron-majority`

- Focus: long-history linearly separable branch
- Trace config: `branches=96` · `seed=13`
- Winner sequence: 64b:perceptron → 128b:perceptron → 256b:gshare → 512b:perceptron → 1024b:perceptron
- Crossover points: 128→256b perceptron→gshare | 256→512b gshare→perceptron
- SVG matrix callouts: 128→256b marks perceptron → gshare; 256→512b marks gshare → perceptron

| Budget | Winner | Runner-up | Matrix callout | Best simple | Best advanced |
| ---: | --- | --- | --- | --- | --- |
| `64` | `perceptron` `82.29%` | `gshare` (`1.04 pp` gap) | - | `always-not-taken` `75.00%` | `perceptron` `82.29%` |
| `128` | `perceptron` `82.29%` | `gshare` (`1.04 pp` gap) | - | `always-not-taken` `75.00%` | `perceptron` `82.29%` |
| `256` | `gshare` `83.33%` | `perceptron` (`1.04 pp` gap) | `128→256b` `perceptron → gshare` | `always-not-taken` `75.00%` | `gshare` `83.33%` |
| `512` | `perceptron` `92.71%` | `gshare` (`9.38 pp` gap) | `256→512b` `gshare → perceptron` | `always-not-taken` `75.00%` | `perceptron` `92.71%` |
| `1024` | `perceptron` `92.71%` | `tournament` (`0.00 pp` gap) | - | `always-not-taken` `75.00%` | `perceptron` `92.71%` |

Representative best-fit configs:
- `64 bits` → perceptron 82.29% (perceptron · table=4 · history=2 · w=15 · bits=62); gshare 81.25% (gshare · table=4 · history=2 · bits=10); local-history 81.25% (local-history · table=4 · history=2 · bits=16)
- `128 bits` → perceptron 82.29% (perceptron · table=4 · history=2 · w=15 · bits=62); gshare 81.25% (gshare · table=4 · history=2 · bits=10); local-history 81.25% (local-history · table=4 · history=2 · bits=16)
- `256 bits` → gshare 83.33% (gshare · table=64 · history=8 · bits=136); perceptron 82.29% (perceptron · table=4 · history=2 · w=15 · bits=62); local-history 81.25% (local-history · table=4 · history=2 · bits=16)
- `512 bits` → perceptron 92.71% (perceptron · table=4 · history=12 · w=15 · bits=272); gshare 83.33% (gshare · table=64 · history=8 · bits=136); local-history 81.25% (local-history · table=4 · history=2 · bits=16)
- `1024 bits` → perceptron 92.71% (perceptron · table=4 · history=12 · w=15 · bits=272); tournament 92.71% (tournament · table=4 · history=8 · bits=568); local-history 90.62% (local-history · table=4 · history=8 · bits=544)

## Portfolio usage

- Use this report when you want to show that ‘best predictor’ depends not only on the trace family, but also on the hardware budget you are willing to spend.
- Use the new whole-grid summary before diving into per-workload rows when you want one fast answer for which predictors dominate the entire budget grid most often.
- Use the margin-trend section when you want to point out that some budget winners are basically photo finishes while others create real separation from the runner-up.
- Use the crossover section when you want the exact budget step that triggers an architecture change instead of only a winner-at-each-budget table, and point at the blue flip chips on the SVG matrix when you need the screenshot to show that trigger directly.
- Pair it with the trace-family sweep and perceptron tuning artifact so you can discuss workload sensitivity, hardware budget, and parameter tuning as three separate design axes.
- The budget-normalized view is especially useful in interviews because it turns a raw accuracy chart into an architecture trade-off conversation.
- Import the CSV export into spreadsheets or slide-deck tooling when you want to chart winner changes across budgets without scraping Markdown.

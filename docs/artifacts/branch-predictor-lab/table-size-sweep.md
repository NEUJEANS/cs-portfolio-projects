# Branch predictor alias table-size sweep

- Generated: `2026-04-18T04:25:43Z`
- Workloads: `5` synthetic families
- Table sizes: `4, 8, 16, 32, 64`
- Goal: compare static PC-index aliasing and dynamic gshare live collisions side by side across the same workload family as table size changes.
- Dynamic note: gshare collisions do not have to fall monotonically because XORed history bits can reshuffle which branch-history contexts share each counter bucket.

## Overview

| Workload | History bits | `4` entries | `8` entries | `16` entries | `32` entries | `64` entries |
| --- | ---: | --- | --- | --- | --- | --- |
| `loop-heavy` | `4` | `S1/G3` | `S1/G4` | `S1/G5` | `S1/G5` | `S0/G0` |
| `random-biased` | `2` | `S1/G4` | `S1/G4` | `S1/G4` | `S2/G8` | `S0/G0` |
| `tournament-style` | `4` | `S1/G4` | `S1/G6` | `S1/G8` | `S2/G6` | `S0/G0` |
| `alias-thrash` | `4` | `S1/G4` | `S2/G8` | `S2/G10` | `S0/G5` | `S0/G5` |
| `perceptron-majority` | `12` | `S0/G3` | `S0/G4` | `S0/G5` | `S0/G5` | `S0/G5` |

## Per-workload notes

### `loop-heavy`

- Focus: loop backedges and exits
- Trace config: `branches=40` · `seed=7` · `history=4`
- Lowest static PC-collision count appears at table size `64`; lowest dynamic gshare collision count appears at table size `64`.
- Sweep delta from smallest to largest table: static `1 → 0` · dynamic `3 → 0` live collisions.

| Table entries | Static collisions | Static conflicting | Static events | Dynamic collisions | Dynamic conflicting | Cross-PC dynamic | History-spread dynamic | Two-bit acc. | Gshare acc. |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `4` | `1` | `0` | `40` | `3` | `1` | `3` | `2` | `80.00%` | `80.00%` |
| `8` | `1` | `0` | `40` | `4` | `1` | `4` | `2` | `80.00%` | `75.00%` |
| `16` | `1` | `0` | `40` | `5` | `2` | `5` | `0` | `80.00%` | `82.50%` |
| `32` | `1` | `0` | `28` | `5` | `1` | `5` | `0` | `80.00%` | `87.50%` |
| `64` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `80.00%` | `90.00%` |

Interpretation tips:
- Static counts answer: 'how many PCs collide if the table indexes only by PC bits?'
- Dynamic counts answer: 'how many live gshare buckets still merge multiple PC+history contexts after XORing in global history?'
- The paired accuracy columns keep the alias numbers grounded so interviewers can see when fewer collisions actually translate into fewer mispredictions.

### `random-biased`

- Focus: biased hot/cold guard branches
- Trace config: `branches=96` · `seed=11` · `history=2`
- Lowest static PC-collision count appears at table size `64`; lowest dynamic gshare collision count appears at table size `64`.
- Sweep delta from smallest to largest table: static `1 → 0` · dynamic `4 → 0` live collisions.

| Table entries | Static collisions | Static conflicting | Static events | Dynamic collisions | Dynamic conflicting | Cross-PC dynamic | History-spread dynamic | Two-bit acc. | Gshare acc. |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `4` | `1` | `1` | `96` | `4` | `4` | `4` | `0` | `46.88%` | `42.71%` |
| `8` | `1` | `1` | `96` | `4` | `4` | `4` | `0` | `46.88%` | `42.71%` |
| `16` | `1` | `1` | `96` | `4` | `4` | `4` | `0` | `46.88%` | `42.71%` |
| `32` | `2` | `2` | `96` | `8` | `5` | `8` | `0` | `52.08%` | `45.83%` |
| `64` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `63.54%` | `54.17%` |

Interpretation tips:
- Static counts answer: 'how many PCs collide if the table indexes only by PC bits?'
- Dynamic counts answer: 'how many live gshare buckets still merge multiple PC+history contexts after XORing in global history?'
- The paired accuracy columns keep the alias numbers grounded so interviewers can see when fewer collisions actually translate into fewer mispredictions.

### `tournament-style`

- Focus: mixed local/global correlation
- Trace config: `branches=48` · `seed=5` · `history=4`
- Lowest static PC-collision count appears at table size `64`; lowest dynamic gshare collision count appears at table size `64`.
- Sweep delta from smallest to largest table: static `1 → 0` · dynamic `4 → 0` live collisions.

| Table entries | Static collisions | Static conflicting | Static events | Dynamic collisions | Dynamic conflicting | Cross-PC dynamic | History-spread dynamic | Two-bit acc. | Gshare acc. |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `4` | `1` | `1` | `48` | `4` | `4` | `4` | `4` | `52.08%` | `60.42%` |
| `8` | `1` | `1` | `48` | `6` | `4` | `6` | `4` | `52.08%` | `68.75%` |
| `16` | `1` | `1` | `48` | `8` | `4` | `8` | `0` | `52.08%` | `72.92%` |
| `32` | `2` | `2` | `48` | `6` | `2` | `6` | `0` | `43.75%` | `77.08%` |
| `64` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `54.17%` | `75.00%` |

Interpretation tips:
- Static counts answer: 'how many PCs collide if the table indexes only by PC bits?'
- Dynamic counts answer: 'how many live gshare buckets still merge multiple PC+history contexts after XORing in global history?'
- The paired accuracy columns keep the alias numbers grounded so interviewers can see when fewer collisions actually translate into fewer mispredictions.

### `alias-thrash`

- Focus: small-table alias interference
- Trace config: `branches=64` · `seed=7` · `history=4`
- Lowest static PC-collision count appears at table size `32`; lowest dynamic gshare collision count appears at table size `4`.
- Sweep delta from smallest to largest table: static `1 → 0` · dynamic `4 → 5` live collisions.

| Table entries | Static collisions | Static conflicting | Static events | Dynamic collisions | Dynamic conflicting | Cross-PC dynamic | History-spread dynamic | Two-bit acc. | Gshare acc. |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `4` | `1` | `1` | `64` | `4` | `3` | `4` | `4` | `50.00%` | `75.00%` |
| `8` | `2` | `2` | `64` | `8` | `4` | `8` | `7` | `50.00%` | `73.44%` |
| `16` | `2` | `2` | `64` | `10` | `3` | `10` | `8` | `50.00%` | `73.44%` |
| `32` | `0` | `0` | `0` | `5` | `1` | `5` | `5` | `79.69%` | `76.56%` |
| `64` | `0` | `0` | `0` | `5` | `1` | `5` | `5` | `79.69%` | `76.56%` |

Interpretation tips:
- Static counts answer: 'how many PCs collide if the table indexes only by PC bits?'
- Dynamic counts answer: 'how many live gshare buckets still merge multiple PC+history contexts after XORing in global history?'
- The paired accuracy columns keep the alias numbers grounded so interviewers can see when fewer collisions actually translate into fewer mispredictions.

### `perceptron-majority`

- Focus: long-history linearly separable branch
- Trace config: `branches=96` · `seed=13` · `history=12`
- Lowest static PC-collision count appears at table size `4`; lowest dynamic gshare collision count appears at table size `4`.
- Sweep delta from smallest to largest table: static `0 → 0` · dynamic `3 → 5` live collisions.

| Table entries | Static collisions | Static conflicting | Static events | Dynamic collisions | Dynamic conflicting | Cross-PC dynamic | History-spread dynamic | Two-bit acc. | Gshare acc. |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `4` | `0` | `0` | `0` | `3` | `2` | `0` | `3` | `73.96%` | `81.25%` |
| `8` | `0` | `0` | `0` | `4` | `2` | `0` | `4` | `73.96%` | `79.17%` |
| `16` | `0` | `0` | `0` | `5` | `2` | `0` | `5` | `73.96%` | `78.12%` |
| `32` | `0` | `0` | `0` | `5` | `2` | `0` | `5` | `73.96%` | `75.00%` |
| `64` | `0` | `0` | `0` | `5` | `1` | `0` | `5` | `73.96%` | `83.33%` |

Interpretation tips:
- Static counts answer: 'how many PCs collide if the table indexes only by PC bits?'
- Dynamic counts answer: 'how many live gshare buckets still merge multiple PC+history contexts after XORing in global history?'
- The paired accuracy columns keep the alias numbers grounded so interviewers can see when fewer collisions actually translate into fewer mispredictions.

## Portfolio usage

- Use this artifact after the single-trace alias-thrash comparison card when you want to show that static and dynamic aliasing shrink differently as the predictor table grows.
- Use the CSV export when you want to chart collision counts or overlay accuracy/collision trade-offs in slides without scraping Markdown.
- The non-monotonic dynamic rows are useful interview material because they show that history-aware predictors change the indexing problem rather than simply eliminating aliasing.

# Branch predictor budget-normalized sweep

- Generated: `2026-04-18T04:05:15Z`
- Workloads: `5` synthetic families
- Compared budgets: `64 bits, 128 bits, 256 bits, 512 bits, 1024 bits`
- Search space: table sizes `4, 8, 16, 32, 64` · history bits `1, 2, 4, 8, 12` · perceptron weight limits `15, 31, 74`
- Goal: compare the best config each predictor can afford under the same approximate state-bit budget instead of one fixed table/history setting for everyone.
- Export note: pair this Markdown report with the committed CSV winner matrix when you want spreadsheet/chart-friendly reuse without re-parsing the table blocks.

## Overview

| Workload | `64 bits` | `128 bits` | `256 bits` | `512 bits` | `1024 bits` |
| --- | --- | --- | --- | --- | --- |
| `loop-heavy` | `gshare` 82.50% | `gshare` 87.50% | `gshare` 90.00% | `gshare` 90.00% | `gshare` 90.00% |
| `random-biased` | `always-taken` 52.08% | `two-bit` 63.54% | `two-bit` 63.54% | `two-bit` 63.54% | `two-bit` 63.54% |
| `tournament-style` | `gshare` 72.92% | `gshare` 77.08% | `gshare` 77.08% | `tournament` 83.33% | `tournament` 83.33% |
| `alias-thrash` | `local-history` 79.69% | `gshare` 81.25% | `gshare` 81.25% | `gshare` 81.25% | `gshare` 81.25% |
| `perceptron-majority` | `perceptron` 82.29% | `perceptron` 82.29% | `gshare` 83.33% | `perceptron` 92.71% | `perceptron` 92.71% |

## Per-workload notes

### `loop-heavy`

- Focus: loop backedges and exits
- Trace config: `branches=40` · `seed=7`
- Winner sequence: 64b:gshare → 128b:gshare → 256b:gshare → 512b:gshare → 1024b:gshare

| Budget | Winner | Runner-up | Best simple | Best advanced |
| ---: | --- | --- | --- | --- |
| `64` | `gshare` `82.50%` | `local-history` (`0.00 pp` gap) | `always-taken` `80.00%` | `gshare` `82.50%` |
| `128` | `gshare` `87.50%` | `local-history` (`5.00 pp` gap) | `always-taken` `80.00%` | `gshare` `87.50%` |
| `256` | `gshare` `90.00%` | `local-history` (`7.50 pp` gap) | `always-taken` `80.00%` | `gshare` `90.00%` |
| `512` | `gshare` `90.00%` | `tournament` (`5.00 pp` gap) | `always-taken` `80.00%` | `gshare` `90.00%` |
| `1024` | `gshare` `90.00%` | `tournament` (`5.00 pp` gap) | `always-taken` `80.00%` | `gshare` `90.00%` |

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

| Budget | Winner | Runner-up | Best simple | Best advanced |
| ---: | --- | --- | --- | --- |
| `64` | `always-taken` `52.08%` | `two-bit` (`0.00 pp` gap) | `always-taken` `52.08%` | `local-history` `51.04%` |
| `128` | `two-bit` `63.54%` | `gshare` (`10.42 pp` gap) | `two-bit` `63.54%` | `gshare` `53.12%` |
| `256` | `two-bit` `63.54%` | `gshare` (`3.12 pp` gap) | `two-bit` `63.54%` | `gshare` `60.42%` |
| `512` | `two-bit` `63.54%` | `gshare` (`3.12 pp` gap) | `two-bit` `63.54%` | `gshare` `60.42%` |
| `1024` | `two-bit` `63.54%` | `perceptron` (`2.08 pp` gap) | `two-bit` `63.54%` | `perceptron` `61.46%` |

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

| Budget | Winner | Runner-up | Best simple | Best advanced |
| ---: | --- | --- | --- | --- |
| `64` | `gshare` `72.92%` | `local-history` (`0.00 pp` gap) | `one-bit` `68.75%` | `gshare` `72.92%` |
| `128` | `gshare` `77.08%` | `local-history` (`0.00 pp` gap) | `one-bit` `68.75%` | `gshare` `77.08%` |
| `256` | `gshare` `77.08%` | `local-history` (`0.00 pp` gap) | `one-bit` `68.75%` | `gshare` `77.08%` |
| `512` | `tournament` `83.33%` | `gshare` (`6.25 pp` gap) | `one-bit` `68.75%` | `tournament` `83.33%` |
| `1024` | `tournament` `83.33%` | `perceptron` (`4.17 pp` gap) | `one-bit` `68.75%` | `tournament` `83.33%` |

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

| Budget | Winner | Runner-up | Best simple | Best advanced |
| ---: | --- | --- | --- | --- |
| `64` | `local-history` `79.69%` | `perceptron` (`0.00 pp` gap) | `two-bit` `79.69%` | `local-history` `79.69%` |
| `128` | `gshare` `81.25%` | `local-history` (`1.56 pp` gap) | `two-bit` `79.69%` | `gshare` `81.25%` |
| `256` | `gshare` `81.25%` | `local-history` (`1.56 pp` gap) | `two-bit` `79.69%` | `gshare` `81.25%` |
| `512` | `gshare` `81.25%` | `perceptron` (`0.00 pp` gap) | `two-bit` `79.69%` | `gshare` `81.25%` |
| `1024` | `gshare` `81.25%` | `perceptron` (`0.00 pp` gap) | `two-bit` `79.69%` | `gshare` `81.25%` |

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

| Budget | Winner | Runner-up | Best simple | Best advanced |
| ---: | --- | --- | --- | --- |
| `64` | `perceptron` `82.29%` | `gshare` (`1.04 pp` gap) | `always-not-taken` `75.00%` | `perceptron` `82.29%` |
| `128` | `perceptron` `82.29%` | `gshare` (`1.04 pp` gap) | `always-not-taken` `75.00%` | `perceptron` `82.29%` |
| `256` | `gshare` `83.33%` | `perceptron` (`1.04 pp` gap) | `always-not-taken` `75.00%` | `gshare` `83.33%` |
| `512` | `perceptron` `92.71%` | `gshare` (`9.38 pp` gap) | `always-not-taken` `75.00%` | `perceptron` `92.71%` |
| `1024` | `perceptron` `92.71%` | `tournament` (`0.00 pp` gap) | `always-not-taken` `75.00%` | `perceptron` `92.71%` |

Representative best-fit configs:
- `64 bits` → perceptron 82.29% (perceptron · table=4 · history=2 · w=15 · bits=62); gshare 81.25% (gshare · table=4 · history=2 · bits=10); local-history 81.25% (local-history · table=4 · history=2 · bits=16)
- `128 bits` → perceptron 82.29% (perceptron · table=4 · history=2 · w=15 · bits=62); gshare 81.25% (gshare · table=4 · history=2 · bits=10); local-history 81.25% (local-history · table=4 · history=2 · bits=16)
- `256 bits` → gshare 83.33% (gshare · table=64 · history=8 · bits=136); perceptron 82.29% (perceptron · table=4 · history=2 · w=15 · bits=62); local-history 81.25% (local-history · table=4 · history=2 · bits=16)
- `512 bits` → perceptron 92.71% (perceptron · table=4 · history=12 · w=15 · bits=272); gshare 83.33% (gshare · table=64 · history=8 · bits=136); local-history 81.25% (local-history · table=4 · history=2 · bits=16)
- `1024 bits` → perceptron 92.71% (perceptron · table=4 · history=12 · w=15 · bits=272); tournament 92.71% (tournament · table=4 · history=8 · bits=568); local-history 90.62% (local-history · table=4 · history=8 · bits=544)

## Portfolio usage

- Use this report when you want to show that ‘best predictor’ depends not only on the trace family, but also on the hardware budget you are willing to spend.
- Pair it with the trace-family sweep and perceptron tuning artifact so you can discuss workload sensitivity, hardware budget, and parameter tuning as three separate design axes.
- The budget-normalized view is especially useful in interviews because it turns a raw accuracy chart into an architecture trade-off conversation.
- Import the CSV export into spreadsheets or slide-deck tooling when you want to chart winner changes across budgets without scraping Markdown.

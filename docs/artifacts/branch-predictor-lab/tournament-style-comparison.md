# Branch predictor comparison card: `tournament-style-seed5`

- Generated: `2026-04-18T03:03:10Z`
- Trace: `artifacts/branch-predictor-lab/tournament-style-seed5.trace`
- Branches: `48` across `4` static PCs
- Taken rate: `58.333%` (`28` taken / `20` not taken)
- Predictor config: table size `16` · history bits `4`

## Headline

- Best predictor: `perceptron` at `77.08%` accuracy with `11` mispredictions.
- Weakest predictor on this trace: `always-not-taken` at `41.67%` accuracy.

## Ranking

| Predictor | Accuracy | Mispredictions | MPKI | Hardest branch |
| --- | ---: | ---: | ---: | --- |
| `perceptron` | `77.08%` | `11` | `229.2` | `0x100` |
| `gshare` | `72.92%` | `13` | `270.8` | `0x100` |
| `local-history` | `72.92%` | `13` | `270.8` | `0x100` |
| `tournament` | `72.92%` | `13` | `270.8` | `0x100` |
| `one-bit` | `68.75%` | `15` | `312.5` | `0x340` |
| `always-taken` | `58.33%` | `20` | `416.7` | `0x340` |
| `two-bit` | `52.08%` | `23` | `479.2` | `0x340` |
| `always-not-taken` | `41.67%` | `28` | `583.3` | `0x100` |

## Portfolio talking points

- perceptron wins this trace at 77.08% accuracy, beating gshare by 4.17 percentage points.
- Two-bit vs one-bit: 52.08% vs 68.75% accuracy (16.67 pp in favor of one-bit on this trace).
- Best advanced predictor: perceptron at 77.08% vs best simple baseline one-bit at 68.75%.
- Static table aliasing: 1 colliding indices at table size 16 (1 with conflicting taken/not-taken biases).
- Dynamic gshare aliasing: 8 live index collisions at table size 16 with history=4 (4 conflicting bias groups).

## Trace mix

- Top PCs: `0x100` × `12`, `0x340` × `12`, `0x380` × `12`, `0x3c0` × `12`
- Top labels: `biased-cleanup` × `12`, `history-driver` × `12`, `history-follower` × `12`, `loop-backedge` × `9`, `loop-exit` × `3`

## Table aliasing

- `1` colliding index groups at table size `16`; `1` groups mix opposite dominant biases.
- `48` branch events land in colliding buckets on this trace.
- Index `0x0`: `0x100` (75.0% taken), `0x340` (50.0% taken), `0x380` (50.0% taken), `0x3c0` (58.3% taken) · `48` events · conflicting biases.

## Dynamic gshare aliasing

- `8` live gshare index groups collide at table size `16` with history bits `4`; `4` groups mix opposite dominant biases.
- `8` groups merge different PCs; `0` groups merge multiple global-history states.
- `43` branch events land in dynamic gshare collisions on this trace.
- Index `0xf`: `0x100@1111` (100.0% taken), `0x340@1111` (0.0% taken), `0x3c0@1111` (0.0% taken) · `8` events · conflicting biases.
- Index `0xc`: `0x100@1100` (66.7% taken), `0x380@1100` (0.0% taken) · `6` events · conflicting biases.
- Index `0x0`: `0x340@0000` (100.0% taken), `0x3c0@0000` (50.0% taken) · `4` events · conflicting biases.
- Index `0x8`: `0x100@1000` (33.3% taken), `0x3c0@1000` (100.0% taken) · `4` events · conflicting biases.
- Index `0x7`: `0x100@0111` (100.0% taken), `0x380@0111` (100.0% taken), `0x3c0@0111` (100.0% taken) · `6` events · similar biases.

## Hardest branches for the winning predictor

- `0x100` · `6` mispredictions over `12` executions (`50.00%` accuracy on that branch)
- `0x3c0` · `4` mispredictions over `12` executions (`66.67%` accuracy on that branch)
- `0x340` · `1` mispredictions over `12` executions (`91.67%` accuracy on that branch)

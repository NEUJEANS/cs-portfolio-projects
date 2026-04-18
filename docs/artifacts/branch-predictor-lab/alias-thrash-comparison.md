# Branch predictor comparison card: `alias-thrash-seed7`

- Generated: `2026-04-18T03:03:10Z`
- Trace: `artifacts/branch-predictor-lab/alias-thrash-seed7.trace`
- Branches: `48` across `4` static PCs
- Taken rate: `56.250%` (`27` taken / `21` not taken)
- Predictor config: table size `16` · history bits `4`

## Headline

- Best predictor: `perceptron` at `77.08%` accuracy with `11` mispredictions.
- Weakest predictor on this trace: `one-bit` at `25.00%` accuracy.

## Ranking

| Predictor | Accuracy | Mispredictions | MPKI | Hardest branch |
| --- | ---: | ---: | ---: | --- |
| `perceptron` | `77.08%` | `11` | `229.2` | `0x150` |
| `local-history` | `72.92%` | `13` | `270.8` | `0x150` |
| `gshare` | `70.83%` | `14` | `291.7` | `0x150` |
| `tournament` | `70.83%` | `14` | `291.7` | `0x140` |
| `always-taken` | `56.25%` | `21` | `437.5` | `0x150` |
| `two-bit` | `56.25%` | `21` | `437.5` | `0x140` |
| `always-not-taken` | `43.75%` | `27` | `562.5` | `0x100` |
| `one-bit` | `25.00%` | `36` | `750.0` | `0x140` |

## Portfolio talking points

- perceptron wins this trace at 77.08% accuracy, beating local-history by 4.17 percentage points.
- Two-bit vs one-bit: 56.25% vs 25.00% accuracy (31.25 pp in favor of two-bit).
- Best advanced predictor: perceptron at 77.08% vs best simple baseline always-taken at 56.25%.
- Static table aliasing: 2 colliding indices at table size 16 (2 with conflicting taken/not-taken biases).
- Dynamic gshare aliasing: 8 live index collisions at table size 16 with history=4 (3 conflicting bias groups).

## Trace mix

- Top PCs: `0x100` × `12`, `0x110` × `12`, `0x140` × `12`, `0x150` × `12`
- Top labels: `alias-cold-not-a` × `12`, `alias-cold-not-b` × `12`, `alias-hot-taken-a` × `12`, `alias-hot-taken-b` × `12`

## Table aliasing

- `2` colliding index groups at table size `16`; `2` groups mix opposite dominant biases.
- `48` branch events land in colliding buckets on this trace.
- Index `0x0`: `0x100` (91.7% taken), `0x140` (25.0% taken) · `24` events · conflicting biases.
- Index `0x4`: `0x110` (91.7% taken), `0x150` (16.7% taken) · `24` events · conflicting biases.

## Dynamic gshare aliasing

- `8` live gshare index groups collide at table size `16` with history bits `4`; `3` groups mix opposite dominant biases.
- `8` groups merge different PCs; `6` groups merge multiple global-history states.
- `37` branch events land in dynamic gshare collisions on this trace.
- Index `0x7`: `0x110@0011` (100.0% taken), `0x140@0111` (0.0% taken) · `3` events · conflicting biases.
- Index `0x9`: `0x140@1001` (100.0% taken), `0x150@1101` (0.0% taken) · `3` events · conflicting biases.
- Index `0x6`: `0x110@0010` (100.0% taken), `0x150@0010` (0.0% taken) · `2` events · conflicting biases.
- Index `0x1`: `0x140@0001` (0.0% taken), `0x150@0101` (28.6% taken) · `8` events · similar biases.
- Index `0xa`: `0x100@1010` (83.3% taken), `0x110@1110` (100.0% taken) · `8` events · similar biases.

## Hardest branches for the winning predictor

- `0x150` · `5` mispredictions over `12` executions (`58.33%` accuracy on that branch)
- `0x100` · `3` mispredictions over `12` executions (`75.00%` accuracy on that branch)
- `0x140` · `3` mispredictions over `12` executions (`75.00%` accuracy on that branch)

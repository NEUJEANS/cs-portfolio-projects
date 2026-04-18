# Branch predictor comparison card: `perceptron-majority-seed13`

- Generated: `2026-04-18T03:03:10Z`
- Trace: `artifacts/branch-predictor-lab/perceptron-majority-seed13.trace`
- Branches: `96` across `1` static PCs
- Taken rate: `25.000%` (`24` taken / `72` not taken)
- Predictor config: table size `32` · history bits `12`

## Headline

- Best predictor: `perceptron` at `92.71%` accuracy with `7` mispredictions.
- Weakest predictor on this trace: `always-taken` at `25.00%` accuracy.

## Ranking

| Predictor | Accuracy | Mispredictions | MPKI | Hardest branch |
| --- | ---: | ---: | ---: | --- |
| `perceptron` | `92.71%` | `7` | `72.9` | `0x480` |
| `local-history` | `88.54%` | `11` | `114.6` | `0x480` |
| `tournament` | `87.50%` | `12` | `125.0` | `0x480` |
| `always-not-taken` | `75.00%` | `24` | `250.0` | `0x480` |
| `gshare` | `75.00%` | `24` | `250.0` | `0x480` |
| `two-bit` | `73.96%` | `25` | `260.4` | `0x480` |
| `one-bit` | `50.00%` | `48` | `500.0` | `0x480` |
| `always-taken` | `25.00%` | `72` | `750.0` | `0x480` |

## Portfolio talking points

- perceptron wins this trace at 92.71% accuracy, beating local-history by 4.17 percentage points.
- Two-bit vs one-bit: 73.96% vs 50.00% accuracy (23.96 pp in favor of two-bit).
- Best advanced predictor: perceptron at 92.71% vs best simple baseline always-not-taken at 75.00%.
- Dynamic gshare aliasing: 5 live index collisions at table size 32 with history=12 (2 conflicting bias groups).
- Worst gshare bucket: index 0x0 mixes 0x480@000000000000, 0x480@001010100000, 0x480@010101000000 across 24 branch events.

## Trace mix

- Top PCs: `0x480` × `96`
- Top labels: `perceptron-majority-target` × `96`

## Table aliasing

- `0` colliding index groups at table size `32`; `0` groups mix opposite dominant biases.
- `0` branch events land in colliding buckets on this trace.
- No static PC aliasing for this table size.

## Dynamic gshare aliasing

- `5` live gshare index groups collide at table size `32` with history bits `12`; `2` groups mix opposite dominant biases.
- `0` groups merge different PCs; `5` groups merge multiple global-history states.
- `64` branch events land in dynamic gshare collisions on this trace.
- Index `0x0`: `0x480@000000000000` (100.0% taken), `0x480@001010100000` (0.0% taken), `0x480@010101000000` (0.0% taken), `0x480@101010000000` (100.0% taken) · `24` events · conflicting biases.
- Index `0xa`: `0x480@000000001010` (100.0% taken), `0x480@000000101010` (0.0% taken), `0x480@100000001010` (100.0% taken) · `16` events · conflicting biases.
- Index `0x1`: `0x480@000000000001` (0.0% taken), `0x480@010100000001` (0.0% taken) · `8` events · similar biases.
- Index `0x2`: `0x480@000000000010` (100.0% taken), `0x480@101000000010` (100.0% taken) · `8` events · similar biases.
- Index `0x5`: `0x480@000000000101` (0.0% taken), `0x480@010000000101` (0.0% taken) · `8` events · similar biases.

## Hardest branches for the winning predictor

- `0x480` · `7` mispredictions over `96` executions (`92.71%` accuracy on that branch)

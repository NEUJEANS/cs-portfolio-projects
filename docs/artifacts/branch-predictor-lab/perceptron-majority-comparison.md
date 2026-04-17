# Branch predictor comparison card: `perceptron-majority-seed13`

- Generated: `2026-04-17T16:43:51Z`
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
- Hardest branch for the winning predictor is 0x480 with 7 misses across 96 executions.
- Top labeled branch motifs: perceptron-majority-target (96).

## Trace mix

- Top PCs: `0x480` × `96`
- Top labels: `perceptron-majority-target` × `96`

## Table aliasing

- `0` colliding index groups at table size `32`; `0` groups mix opposite dominant biases.
- `0` branch events land in colliding buckets on this trace.
- No static PC aliasing for this table size.

## Hardest branches for the winning predictor

- `0x480` · `7` mispredictions over `96` executions (`92.71%` accuracy on that branch)

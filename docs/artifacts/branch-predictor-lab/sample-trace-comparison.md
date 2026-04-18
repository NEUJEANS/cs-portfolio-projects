# Branch predictor comparison card: `sample_trace`

- Generated: `2026-04-18T03:03:10Z`
- Trace: `projects/branch-predictor-lab/sample_trace.txt`
- Branches: `24` across `4` static PCs
- Taken rate: `62.500%` (`15` taken / `9` not taken)
- Predictor config: table size `16` · history bits `2`

## Headline

- Best predictor: `local-history` at `75.00%` accuracy with `6` mispredictions.
- Weakest predictor on this trace: `one-bit` at `25.00%` accuracy.

## Ranking

| Predictor | Accuracy | Mispredictions | MPKI | Hardest branch |
| --- | ---: | ---: | ---: | --- |
| `local-history` | `75.00%` | `6` | `250.0` | `0x100` |
| `perceptron` | `75.00%` | `6` | `250.0` | `0x100` |
| `tournament` | `75.00%` | `6` | `250.0` | `0x100` |
| `gshare` | `70.83%` | `7` | `291.7` | `0x100` |
| `always-taken` | `62.50%` | `9` | `375.0` | `0x140` |
| `two-bit` | `62.50%` | `9` | `375.0` | `0x140` |
| `always-not-taken` | `37.50%` | `15` | `625.0` | `0x100` |
| `one-bit` | `25.00%` | `18` | `750.0` | `0x140` |

## Portfolio talking points

- Top spot is a tie at 75.00% accuracy across local-history, perceptron, tournament.
- Two-bit vs one-bit: 62.50% vs 25.00% accuracy (37.50 pp in favor of two-bit).
- Best advanced predictor: local-history at 75.00% vs best simple baseline always-taken at 62.50%.
- Static table aliasing: 1 colliding indices at table size 16 (1 with conflicting taken/not-taken biases).
- Dynamic gshare aliasing: 4 live index collisions at table size 16 with history=2 (3 conflicting bias groups).

## Trace mix

- Top PCs: `0x100` × `8`, `0x140` × `8`, `0x200` × `4`, `0x204` × `4`
- Top labels: `alternating-phase` × `8`, `cache-hit` × `3`, `cache-miss` × `1`, `issue-continue` × `2`, `issue-stall` × `2`

## Table aliasing

- `1` colliding index groups at table size `16`; `1` groups mix opposite dominant biases.
- `20` branch events land in colliding buckets on this trace.
- Index `0x0`: `0x100` (75.0% taken), `0x140` (50.0% taken), `0x200` (75.0% taken) · `20` events · conflicting biases.

## Dynamic gshare aliasing

- `4` live gshare index groups collide at table size `16` with history bits `2`; `3` groups mix opposite dominant biases.
- `4` groups merge different PCs; `3` groups merge multiple global-history states.
- `24` branch events land in dynamic gshare collisions on this trace.
- Index `0x2`: `0x100@10` (100.0% taken), `0x140@10` (100.0% taken), `0x200@10` (100.0% taken), `0x204@11` (0.0% taken) · `8` events · conflicting biases.
- Index `0x3`: `0x100@11` (50.0% taken), `0x200@11` (50.0% taken), `0x204@10` (0.0% taken) · `7` events · conflicting biases.
- Index `0x1`: `0x100@01` (100.0% taken), `0x140@01` (0.0% taken) · `6` events · conflicting biases.
- Index `0x0`: `0x100@00` (100.0% taken), `0x204@01` (100.0% taken) · `3` events · similar biases.

## Hardest branches for the winning predictor

- `0x100` · `2` mispredictions over `8` executions (`75.00%` accuracy on that branch)
- `0x140` · `2` mispredictions over `8` executions (`75.00%` accuracy on that branch)
- `0x200` · `2` mispredictions over `4` executions (`50.00%` accuracy on that branch)

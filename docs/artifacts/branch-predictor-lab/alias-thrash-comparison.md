# Branch predictor comparison card: `alias-thrash-seed7`

- Generated: `2026-04-17T10:52:47Z`
- Trace: `artifacts/branch-predictor-lab/alias-thrash-seed7.trace`
- Branches: `48` across `4` static PCs
- Taken rate: `56.250%` (`27` taken / `21` not taken)
- Predictor config: table size `16` · history bits `4`

## Headline

- Best predictor: `local-history` at `72.92%` accuracy with `13` mispredictions.
- Weakest predictor on this trace: `one-bit` at `25.00%` accuracy.

## Ranking

| Predictor | Accuracy | Mispredictions | MPKI | Hardest branch |
| --- | ---: | ---: | ---: | --- |
| `local-history` | `72.92%` | `13` | `270.8` | `0x150` |
| `gshare` | `70.83%` | `14` | `291.7` | `0x150` |
| `tournament` | `70.83%` | `14` | `291.7` | `0x140` |
| `always-taken` | `56.25%` | `21` | `437.5` | `0x150` |
| `two-bit` | `56.25%` | `21` | `437.5` | `0x140` |
| `always-not-taken` | `43.75%` | `27` | `562.5` | `0x100` |
| `one-bit` | `25.00%` | `36` | `750.0` | `0x140` |

## Portfolio talking points

- local-history wins this trace at 72.92% accuracy, beating gshare by 2.08 percentage points.
- Two-bit vs one-bit: 56.25% vs 25.00% accuracy (31.25 pp in favor of two-bit).
- Best advanced predictor: local-history at 72.92% vs best simple baseline always-taken at 56.25%.
- Hardest branch for the winning predictor is 0x150 with 5 misses across 12 executions.
- Static table aliasing: 2 colliding indices at table size 16 (2 with conflicting taken/not-taken biases).

## Trace mix

- Top PCs: `0x100` × `12`, `0x110` × `12`, `0x140` × `12`, `0x150` × `12`
- Top labels: `alias-cold-not-a` × `12`, `alias-cold-not-b` × `12`, `alias-hot-taken-a` × `12`, `alias-hot-taken-b` × `12`

## Table aliasing

- `2` colliding index groups at table size `16`; `2` groups mix opposite dominant biases.
- `48` branch events land in colliding buckets on this trace.
- Index `0x0`: `0x100` (91.7% taken), `0x140` (25.0% taken) · `24` events · conflicting biases.
- Index `0x4`: `0x110` (91.7% taken), `0x150` (16.7% taken) · `24` events · conflicting biases.

## Hardest branches for the winning predictor

- `0x150` · `5` mispredictions over `12` executions (`58.33%` accuracy on that branch)
- `0x140` · `4` mispredictions over `12` executions (`66.67%` accuracy on that branch)
- `0x100` · `2` mispredictions over `12` executions (`83.33%` accuracy on that branch)
- `0x110` · `2` mispredictions over `12` executions (`83.33%` accuracy on that branch)

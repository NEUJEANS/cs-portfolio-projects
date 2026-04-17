# Branch predictor comparison card: `sample_trace`

- Generated: `2026-04-17T10:22:45Z`
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
| `tournament` | `75.00%` | `6` | `250.0` | `0x100` |
| `gshare` | `70.83%` | `7` | `291.7` | `0x100` |
| `always-taken` | `62.50%` | `9` | `375.0` | `0x140` |
| `two-bit` | `62.50%` | `9` | `375.0` | `0x140` |
| `always-not-taken` | `37.50%` | `15` | `625.0` | `0x100` |
| `one-bit` | `25.00%` | `18` | `750.0` | `0x140` |

## Portfolio talking points

- Top spot is a tie at 75.00% accuracy across local-history, tournament.
- Two-bit vs one-bit: 62.50% vs 25.00% accuracy (37.50 pp in favor of two-bit).
- Best advanced predictor: local-history at 75.00% vs best simple baseline always-taken at 62.50%.
- Hardest branch for the winning predictor is 0x100 with 2 misses across 8 executions.
- Top labeled branch motifs: alternating-phase (8), loop-back (6), cache-hit (3).

## Trace mix

- Top PCs: `0x100` × `8`, `0x140` × `8`, `0x200` × `4`, `0x204` × `4`
- Top labels: `alternating-phase` × `8`, `cache-hit` × `3`, `cache-miss` × `1`, `issue-continue` × `2`, `issue-stall` × `2`

## Hardest branches for the winning predictor

- `0x100` · `2` mispredictions over `8` executions (`75.00%` accuracy on that branch)
- `0x140` · `2` mispredictions over `8` executions (`75.00%` accuracy on that branch)
- `0x200` · `2` mispredictions over `4` executions (`50.00%` accuracy on that branch)

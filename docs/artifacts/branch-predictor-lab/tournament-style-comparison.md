# Branch predictor comparison card: `tournament-style-seed5`

- Generated: `2026-04-17T10:23:46Z`
- Trace: `artifacts/branch-predictor-lab/tournament-style-seed5.trace`
- Branches: `48` across `4` static PCs
- Taken rate: `58.333%` (`28` taken / `20` not taken)
- Predictor config: table size `16` · history bits `4`

## Headline

- Best predictor: `gshare` at `72.92%` accuracy with `13` mispredictions.
- Weakest predictor on this trace: `always-not-taken` at `41.67%` accuracy.

## Ranking

| Predictor | Accuracy | Mispredictions | MPKI | Hardest branch |
| --- | ---: | ---: | ---: | --- |
| `gshare` | `72.92%` | `13` | `270.8` | `0x100` |
| `local-history` | `72.92%` | `13` | `270.8` | `0x100` |
| `tournament` | `72.92%` | `13` | `270.8` | `0x100` |
| `one-bit` | `68.75%` | `15` | `312.5` | `0x340` |
| `always-taken` | `58.33%` | `20` | `416.7` | `0x340` |
| `two-bit` | `52.08%` | `23` | `479.2` | `0x340` |
| `always-not-taken` | `41.67%` | `28` | `583.3` | `0x100` |

## Portfolio talking points

- Top spot is a tie at 72.92% accuracy across gshare, local-history, tournament.
- Two-bit vs one-bit: 52.08% vs 68.75% accuracy (16.67 pp in favor of one-bit on this trace).
- Best advanced predictor: gshare at 72.92% vs best simple baseline one-bit at 68.75%.
- Hardest branch for the winning predictor is 0x100 with 5 misses across 12 executions.
- Top labeled branch motifs: biased-cleanup (12), history-driver (12), history-follower (12).

## Trace mix

- Top PCs: `0x100` × `12`, `0x340` × `12`, `0x380` × `12`, `0x3c0` × `12`
- Top labels: `biased-cleanup` × `12`, `history-driver` × `12`, `history-follower` × `12`, `loop-backedge` × `9`, `loop-exit` × `3`

## Hardest branches for the winning predictor

- `0x100` · `5` mispredictions over `12` executions (`58.33%` accuracy on that branch)
- `0x3c0` · `4` mispredictions over `12` executions (`66.67%` accuracy on that branch)
- `0x380` · `3` mispredictions over `12` executions (`75.00%` accuracy on that branch)
- `0x340` · `1` mispredictions over `12` executions (`91.67%` accuracy on that branch)

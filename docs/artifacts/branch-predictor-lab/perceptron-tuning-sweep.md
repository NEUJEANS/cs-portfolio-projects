# Branch predictor perceptron tuning sweep

- Generated: `2026-04-18T03:30:28Z`
- Trace: `artifacts/branch-predictor-lab/perceptron-majority-seed13.trace`
- Branches: `96` across `1` unique PCs
- Predictor config: `table=32` · `history=12`
- Swept thresholds: `19, 28, 37, 46, 55`
- Swept weight limits: `18, 37, 74, 148`
- Default heuristic: `threshold=37` · `weight_limit=74`

## Headlines

- Best config: `threshold=19` · `weight_limit=74` → `93.75%` accuracy with `6` mispredictions.
- Default heuristic: `92.71%` accuracy with `7` mispredictions (+1.04 pp vs best).
- Saturation visible in `5` / `20` swept configs (`max|w|` hit the clamp limit).

## Accuracy matrix

| Threshold ↓ / Weight limit → | `18` | `37` | `74` | `148` |
| --- | ---: | ---: | ---: | ---: |
| `19` | 93.75% | 93.75% | 93.75% (best) | 93.75% |
| `28` | 92.71% (sat) | 92.71% | 92.71% | 92.71% |
| `37` | 92.71% (sat) | 92.71% | 92.71% (default) | 92.71% |
| `46` | 92.71% (sat) | 92.71% | 92.71% | 92.71% |
| `55` | 92.71% (sat) | 92.71% (sat) | 92.71% | 92.71% |

## Top configs

| Rank | Threshold | Weight limit | Accuracy | Mispredictions | Max abs(w) | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `19` | `74` | `93.75%` | `6` | `17` | best |
| 2 | `19` | `37` | `93.75%` | `6` | `17` | - |
| 3 | `19` | `18` | `93.75%` | `6` | `17` | - |
| 4 | `19` | `148` | `93.75%` | `6` | `17` | - |
| 5 | `37` | `74` | `92.71%` | `7` | `29` | default |
| 6 | `37` | `37` | `92.71%` | `7` | `29` | - |
| 7 | `37` | `18` | `92.71%` | `7` | `18` | saturated |
| 8 | `37` | `148` | `92.71%` | `7` | `29` | - |

## Portfolio usage

- Use this report to show that neural branch predictors still need practical tuning; longer history alone is not the whole story.
- Pair it with the perceptron-majority comparison card when you want both a single-trace win story and a parameter-sensitivity artifact.
- Call out saturated low-clamp runs when explaining why hardware-friendly limits can trade off training headroom against stability.

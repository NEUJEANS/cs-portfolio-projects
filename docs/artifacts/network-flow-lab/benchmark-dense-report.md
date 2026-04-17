# Network-flow benchmark report card

- Generated: 2026-04-17T00:47:52Z
- Graph family: `dense`
- Setup: `18` nodes · edge probability `0.3` · capacity range `1-20` · `3` trial(s) · seed `7`
- Family focus: residual-heavy dense meshes that create more rerouting pressure

## Headline

- Dinic averaged 1.10x faster than Edmonds-Karp on this dense suite while using the same average augmenting-path count.
- Mean max flow across trials: `156.0` with mean edge density `0.479`.
- Edmonds-Karp mean runtime: `0.83` ms with `30.33` mean augmentations.
- Dinic mean runtime: `0.752` ms with `30.33` mean augmentations and `3.33` mean phases.

## Trial table

| Trial | Seed | Edges | Density | Max flow | Edmonds-Karp ms | EK augmentations | Dinic ms | Dinic augmentations | Dinic phases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 7 | 146 | 0.477 | 169 | 0.833 | 31 | 0.868 | 31 | 4 |
| 2 | 8 | 147 | 0.48 | 167 | 0.994 | 33 | 0.868 | 33 | 4 |
| 3 | 9 | 147 | 0.48 | 132 | 0.664 | 27 | 0.521 | 27 | 2 |

## Portfolio talking points

- `dense` gives you a concrete benchmark story: residual-heavy dense meshes that create more rerouting pressure.
- The trial rows verify both algorithms agreed on every max-flow value, so the timing comparison is paired with a correctness cross-check.
- Augmentation counts and Dinic phase counts make the runtime story easier to explain than a single speed number in isolation.

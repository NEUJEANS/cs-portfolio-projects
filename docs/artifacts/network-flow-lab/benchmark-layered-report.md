# Network-flow benchmark report card

- Generated: 2026-04-17T00:47:53Z
- Graph family: `layered`
- Setup: `18` nodes · edge probability `0.2` · capacity range `1-20` · `3` trial(s) · seed `7`
- Family focus: cut-stress layered networks that highlight blocking-flow phases

## Headline

- Dinic averaged 1.19x faster than Edmonds-Karp on this layered suite while using the same average augmenting-path count.
- Mean max flow across trials: `29.0` with mean edge density `0.222`.
- Edmonds-Karp mean runtime: `0.625` ms with `21.0` mean augmentations.
- Dinic mean runtime: `0.523` ms with `21.0` mean augmentations and `3.0` mean phases.

## Trial table

| Trial | Seed | Edges | Density | Max flow | Edmonds-Karp ms | EK augmentations | Dinic ms | Dinic augmentations | Dinic phases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 7 | 63 | 0.206 | 27 | 0.598 | 20 | 0.535 | 20 | 3 |
| 2 | 8 | 68 | 0.222 | 32 | 0.69 | 25 | 0.493 | 25 | 3 |
| 3 | 9 | 73 | 0.239 | 28 | 0.586 | 18 | 0.542 | 18 | 3 |

## Portfolio talking points

- `layered` gives you a concrete benchmark story: cut-stress layered networks that highlight blocking-flow phases.
- The trial rows verify both algorithms agreed on every max-flow value, so the timing comparison is paired with a correctness cross-check.
- Augmentation counts and Dinic phase counts make the runtime story easier to explain than a single speed number in isolation.

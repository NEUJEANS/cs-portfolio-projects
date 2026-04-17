# Network-flow benchmark report card

- Generated: 2026-04-17T14:46:00Z
- Graph family: `dag`
- Setup: `24` nodes · edge probability `0.18` · capacity range `1-20` · `5` trial(s) · seed `42`
- Family focus: acyclic baseline graphs that keep the benchmark easy to reason about

## Headline

- Edmonds-Karp averaged 1.44x faster than Dinic on this dag suite, which is a useful reminder that small pure-Python workloads can invert the asymptotic story.
- Mean max flow across trials: `26.2` with mean edge density `0.131`.
- Edmonds-Karp mean runtime: `0.241` ms with `7.0` mean augmentations.
- Dinic mean runtime: `0.347` ms with `7.0` mean augmentations and `3.4` mean phases.

## Trial table

| Trial | Seed | Edges | Density | Max flow | Edmonds-Karp ms | EK augmentations | Dinic ms | Dinic augmentations | Dinic phases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 42 | 78 | 0.141 | 28 | 0.282 | 7 | 0.399 | 7 | 3 |
| 2 | 43 | 73 | 0.132 | 23 | 0.213 | 5 | 0.277 | 5 | 2 |
| 3 | 44 | 74 | 0.134 | 21 | 0.181 | 3 | 0.268 | 3 | 2 |
| 4 | 45 | 66 | 0.12 | 34 | 0.312 | 12 | 0.448 | 12 | 6 |
| 5 | 46 | 70 | 0.127 | 25 | 0.217 | 8 | 0.344 | 8 | 4 |

## Portfolio talking points

- `dag` gives you a concrete benchmark story: acyclic baseline graphs that keep the benchmark easy to reason about.
- The trial rows verify both algorithms agreed on every max-flow value, so the timing comparison is paired with a correctness cross-check.
- Augmentation counts and Dinic phase counts make the runtime story easier to explain than a single speed number in isolation.

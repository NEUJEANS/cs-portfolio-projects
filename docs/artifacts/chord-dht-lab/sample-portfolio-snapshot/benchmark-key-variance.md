# Chord benchmark key variance

- Identifier bits: `8`
- Node count: `5`
- Key count: `5`
- Sample count: `3`
- Start nodes per sample: `3`
- Sample seeds: `17`, `29`, `43`
- Highest hop-savings spread: `2`
- Most sensitive key(s): `internship-notes`, `final-project`, `report.pdf`, `slides`, `compiler`

| Key | Responsible node | Avg chord hops | Avg linear hops | Avg hop savings | Hop-savings spread | Chord spread | Start nodes seen | Best seed/start | Worst seed/start |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `internship-notes` | `bravo` | 1.5556 | 2.0 | 0.4444 | 2 | 3 | 5 | `29`/alpha (2), `43`/alpha (2) | `17`/bravo (0), `17`/charlie (0), `17`/echo (0), `29`/bravo (0), `29`/charlie (0), `43`/delta (0), `43`/echo (0) |
| `final-project` | `alpha` | 1.3333 | 1.8889 | 0.5556 | 2 | 2 | 5 | `17`/charlie (2), `29`/charlie (2) | `17`/bravo (0), `17`/echo (0), `29`/alpha (0), `29`/bravo (0), `43`/alpha (0), `43`/echo (0) |
| `report.pdf` | `alpha` | 1.3333 | 1.8889 | 0.5556 | 2 | 2 | 5 | `17`/charlie (2), `29`/charlie (2) | `17`/bravo (0), `17`/echo (0), `29`/alpha (0), `29`/bravo (0), `43`/alpha (0), `43`/echo (0) |
| `slides` | `alpha` | 1.3333 | 1.8889 | 0.5556 | 2 | 2 | 5 | `17`/charlie (2), `29`/charlie (2) | `17`/bravo (0), `17`/echo (0), `29`/alpha (0), `29`/bravo (0), `43`/alpha (0), `43`/echo (0) |
| `compiler` | `charlie` | 1.3333 | 1.7778 | 0.4444 | 2 | 2 | 5 | `43`/delta (2) | `17`/bravo (0), `17`/charlie (0), `29`/alpha (0), `29`/bravo (0), `29`/charlie (0), `43`/alpha (0) |

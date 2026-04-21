# Chord benchmark sample comparison

- Identifier bits: `8`
- Node count: `5`
- Key count: `5`
- Sample count: `3`
- Start nodes per sample: `3`
- Sample seeds: `17`, `29`, `43`
- Cases per sample: `15`
- Total hop savings range: `7` to `8`
- Hop savings spread: `1`
- Strongest sample seed(s): `29`, `43`
- Weakest sample seed(s): `17`

| Seed | Start nodes | Avg Chord hops | Avg linear hops | Total hop savings | Improved | Tied | Slower |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `17` | `bravo`, `echo`, `charlie` | 1.533 | 2 | 7 | 4 | 11 | 0 |
| `29` | `bravo`, `alpha`, `charlie` | 1.133 | 1.667 | 8 | 4 | 11 | 0 |
| `43` | `alpha`, `delta`, `echo` | 1.467 | 2 | 8 | 6 | 9 | 0 |

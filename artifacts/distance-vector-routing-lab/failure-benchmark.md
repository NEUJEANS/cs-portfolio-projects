# Failure benchmark for A → C

Link removal: `B ↔ C`

| mode | update strategy | converged | rounds | changed rounds | active steps | baseline | final | first change | first unreachable | last route change | max cost | max finite cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classic | periodic | True | 16 | 15 | 16 | 2 via B | 16 via unreachable | 2 | 14 | 14 | 16 | 14 |
| split-horizon | periodic | True | 3 | 2 | 3 | 2 via B | 16 via unreachable | 2 | 2 | 2 | 16 | 2 |
| poison-reverse | periodic | True | 3 | 2 | 3 | 2 via B | 16 via unreachable | 2 | 2 | 2 | 16 | 2 |
| classic | triggered | True | 18 | 15 | 18 | 2 via B | 16 via unreachable | 2 | 15 | 15 | 16 | 14 |
| split-horizon | triggered | True | 5 | 2 | 5 | 2 via B | 16 via unreachable | 2 | 2 | 2 | 16 | 2 |
| poison-reverse | triggered | True | 5 | 2 | 5 | 2 via B | 16 via unreachable | 2 | 2 | 2 | 16 | 2 |

## Summary
- fastest reconvergence: `poison-reverse` + `periodic` in 3 rounds
- earliest unreachable: `poison-reverse` + `periodic` at round 2
- lowest peak finite tracked-route cost: `poison-reverse` + `periodic` with max finite cost 2

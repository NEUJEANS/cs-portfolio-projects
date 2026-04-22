# Failure benchmark suite

Infinity metric: 16, max rounds: 50

Curated scenarios: 4

## Scenario roster

| scenario | tracked route | link removal | description |
| --- | --- | --- | --- |
| count-to-infinity-line | A → C | B ↔ C | The classic A-B-C line where removing B-C isolates C and exposes the clean two-router count-to-infinity story. |
| square-detour | A → C | B ↔ C | A four-router square where the watched route survives via a longer alternate path after the primary edge disappears. |
| ring-isolation | A → E | C ↔ E | A four-router ring feeding a destination leaf, useful for showing that larger loops can still bounce even with split horizon or poison reverse. |
| five-node-bypass | A → C | B ↔ C | A five-router topology where the best path breaks, briefly inflates, then settles onto a more expensive but still reachable bypass. |

## Strategy scorecard

| mode | update strategy | scenarios | non-converged | avg rounds | avg last route change | avg max finite cost | fastest wins | earliest unreachable wins | lowest peak wins |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classic | periodic | 4 | 0 | 10.75 | 9.25 | 9.75 | 1 | 0 | 1 |
| split-horizon | periodic | 4 | 0 | 6.75 | 5.25 | 6.75 | 0 | 0 | 0 |
| poison-reverse | periodic | 4 | 0 | 6.75 | 5.25 | 6.75 | 3 | 2 | 3 |
| classic | triggered | 4 | 0 | 17.5 | 12.75 | 9.75 | 0 | 0 | 0 |
| split-horizon | triggered | 4 | 0 | 12.75 | 7.25 | 6.75 | 0 | 0 | 0 |
| poison-reverse | triggered | 4 | 0 | 12.75 | 7.25 | 6.75 | 0 | 0 | 0 |

## Scenario: count-to-infinity-line

The classic A-B-C line where removing B-C isolates C and exposes the clean two-router count-to-infinity story.

- tracked route: `A → C`
- link removal: `B ↔ C`

| mode | update strategy | converged | rounds | changed rounds | active steps | baseline | final | first change | first unreachable | last route change | max cost | max finite cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classic | periodic | True | 16 | 15 | 16 | 2 via B | 16 via unreachable | 2 | 14 | 14 | 16 | 14 |
| split-horizon | periodic | True | 3 | 2 | 3 | 2 via B | 16 via unreachable | 2 | 2 | 2 | 16 | 2 |
| poison-reverse | periodic | True | 3 | 2 | 3 | 2 via B | 16 via unreachable | 2 | 2 | 2 | 16 | 2 |
| classic | triggered | True | 18 | 15 | 18 | 2 via B | 16 via unreachable | 2 | 15 | 15 | 16 | 14 |
| split-horizon | triggered | True | 5 | 2 | 5 | 2 via B | 16 via unreachable | 2 | 2 | 2 | 16 | 2 |
| poison-reverse | triggered | True | 5 | 2 | 5 | 2 via B | 16 via unreachable | 2 | 2 | 2 | 16 | 2 |

- fastest reconvergence: `poison-reverse` + `periodic` in 3 rounds
- earliest unreachable: `poison-reverse` + `periodic` at round 2
- lowest peak finite tracked-route cost: `poison-reverse` + `periodic` with max finite cost 2

## Scenario: square-detour

A four-router square where the watched route survives via a longer alternate path after the primary edge disappears.

- tracked route: `A → C`
- link removal: `B ↔ C`

| mode | update strategy | converged | rounds | changed rounds | active steps | baseline | final | first change | first unreachable | last route change | max cost | max finite cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classic | periodic | True | 5 | 4 | 5 | 3 via B | 5 via D | 2 | None | 4 | 5 | 5 |
| split-horizon | periodic | True | 4 | 3 | 4 | 3 via B | 5 via D | 2 | None | 2 | 5 | 5 |
| poison-reverse | periodic | True | 4 | 3 | 4 | 3 via B | 5 via D | 2 | None | 2 | 5 | 5 |
| classic | triggered | True | 11 | 6 | 11 | 3 via B | 5 via D | 2 | None | 6 | 5 | 5 |
| split-horizon | triggered | True | 10 | 5 | 10 | 3 via B | 5 via D | 2 | None | 2 | 5 | 5 |
| poison-reverse | triggered | True | 10 | 5 | 10 | 3 via B | 5 via D | 2 | None | 2 | 5 | 5 |

- fastest reconvergence: `poison-reverse` + `periodic` in 4 rounds
- earliest unreachable: none
- lowest peak finite tracked-route cost: `poison-reverse` + `periodic` with max finite cost 5

## Scenario: ring-isolation

A four-router ring feeding a destination leaf, useful for showing that larger loops can still bounce even with split horizon or poison reverse.

- tracked route: `A → E`
- link removal: `C ↔ E`

| mode | update strategy | converged | rounds | changed rounds | active steps | baseline | final | first change | first unreachable | last route change | max cost | max finite cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classic | periodic | True | 16 | 15 | 16 | 3 via B | 16 via unreachable | 3 | 15 | 15 | 16 | 15 |
| split-horizon | periodic | True | 16 | 15 | 16 | 3 via B | 16 via unreachable | 3 | 3 | 15 | 16 | 15 |
| poison-reverse | periodic | True | 16 | 15 | 16 | 3 via B | 16 via unreachable | 3 | 3 | 15 | 16 | 15 |
| classic | triggered | True | 27 | 15 | 27 | 3 via B | 16 via unreachable | 4 | 23 | 23 | 16 | 15 |
| split-horizon | triggered | True | 27 | 15 | 27 | 3 via B | 16 via unreachable | 4 | 4 | 23 | 16 | 15 |
| poison-reverse | triggered | True | 27 | 15 | 27 | 3 via B | 16 via unreachable | 4 | 4 | 23 | 16 | 15 |

- fastest reconvergence: `classic` + `periodic` in 16 rounds
- earliest unreachable: `poison-reverse` + `periodic` at round 3
- lowest peak finite tracked-route cost: `classic` + `periodic` with max finite cost 15

## Scenario: five-node-bypass

A five-router topology where the best path breaks, briefly inflates, then settles onto a more expensive but still reachable bypass.

- tracked route: `A → C`
- link removal: `B ↔ C`

| mode | update strategy | converged | rounds | changed rounds | active steps | baseline | final | first change | first unreachable | last route change | max cost | max finite cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classic | periodic | True | 6 | 5 | 6 | 2 via B | 5 via D | 2 | None | 4 | 5 | 5 |
| split-horizon | periodic | True | 4 | 3 | 4 | 2 via B | 5 via D | 2 | None | 2 | 5 | 5 |
| poison-reverse | periodic | True | 4 | 3 | 4 | 2 via B | 5 via D | 2 | None | 2 | 5 | 5 |
| classic | triggered | True | 14 | 7 | 14 | 2 via B | 5 via D | 2 | None | 7 | 5 | 5 |
| split-horizon | triggered | True | 9 | 4 | 9 | 2 via B | 5 via D | 2 | None | 2 | 5 | 5 |
| poison-reverse | triggered | True | 9 | 4 | 9 | 2 via B | 5 via D | 2 | None | 2 | 5 | 5 |

- fastest reconvergence: `poison-reverse` + `periodic` in 4 rounds
- earliest unreachable: none
- lowest peak finite tracked-route cost: `poison-reverse` + `periodic` with max finite cost 5

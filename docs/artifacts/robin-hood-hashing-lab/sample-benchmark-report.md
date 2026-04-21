# Robin Hood hashing benchmark comparison with delete-heavy workloads

Deterministic benchmark report comparing Robin Hood hashing against a linear-probing baseline, with resident probe-distance plus unsuccessful-lookup histograms that make both dispersion and miss cost visible at a glance. It also includes a delete-heavy workload that removes 30.0% of keys before the final hit/miss lookup + histogram pass, so post-removal clustering is visible too.

- Capacity: 31
- Trials per workload/load factor: 3
- Strategies: Robin Hood hashing, Linear probing
- Workloads: Fill-only, Delete-heavy (30.0% removals)
- Requested load factors: 0.25, 0.5, 0.75
- Note: requested load factors are rounded to whole entry counts, so the effective fill level can differ slightly from the requested target.

## Headline comparisons

| Workload | Requested load factor | Remaining load factor | Remaining entries | Successful lookup winner | Success delta vs linear | Unsuccessful lookup winner | Miss delta vs linear | Lower probe-distance stddev | Stddev delta vs linear | Lower delete probes | Delete delta vs linear |
| --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- | ---: | --- | ---: |
| Fill-only | 0.25 | 0.2581 | 8 | Tie | 0 | Linear probing | -0.1667 | Tie | 0 | — | — |
| Fill-only | 0.5 | 0.5161 | 16 | Tie | 0 | Robin Hood hashing | 0.4584 | Robin Hood hashing | 0.0922 | — | — |
| Fill-only | 0.75 | 0.7419 | 23 | Tie | 0 | Robin Hood hashing | 1.6377 | Robin Hood hashing | 0.5469 | — | — |
| Delete-heavy (30.0% removals) | 0.25 | 0.1935 | 6 | Tie | 0 | Robin Hood hashing | 0.2222 | Tie | 0 | Tie | 0 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3548 | 11 | Tie | 0 | Robin Hood hashing | 0.1516 | Robin Hood hashing | 0.0719 | Tie | 0 |
| Delete-heavy (30.0% removals) | 0.75 | 0.5161 | 16 | Tie | 0 | Robin Hood hashing | 0.5834 | Robin Hood hashing | 0.1413 | Tie | 0 |

## Aggregate metrics

| Workload | Requested load factor | Remaining load factor | Strategy | Deleted entries | Avg insert probes | Avg delete probes | Avg successful lookup probes | Avg unsuccessful lookup probes | Avg probe distance | Probe-distance stddev | Max probe distance | Max cluster length | Avg swaps |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fill-only | 0.25 | 0.2581 | Robin Hood hashing | 0 | 1.125 | 0 | 1.125 | 1.375 | 0.125 | 0.3307 | 1 | 5 | 0 |
| Fill-only | 0.25 | 0.2581 | Linear probing | 0 | 1.125 | 0 | 1.125 | 1.2083 | 0.125 | 0.3307 | 1 | 5 | 0 |
| Fill-only | 0.5 | 0.5161 | Robin Hood hashing | 0 | 1.2083 | 0 | 1.2083 | 1.7708 | 0.2083 | 0.4061 | 1 | 7 | 0.6667 |
| Fill-only | 0.5 | 0.5161 | Linear probing | 0 | 1.2083 | 0 | 1.2083 | 2.2292 | 0.2083 | 0.4983 | 2 | 7 | 0 |
| Fill-only | 0.75 | 0.7419 | Robin Hood hashing | 0 | 1.8986 | 0 | 1.8986 | 2.3913 | 0.8986 | 1.0515 | 5 | 14 | 6.6667 |
| Fill-only | 0.75 | 0.7419 | Linear probing | 0 | 1.8986 | 0 | 1.8986 | 4.029 | 0.8986 | 1.5984 | 7 | 14 | 0 |
| Delete-heavy (30.0% removals) | 0.25 | 0.1935 | Robin Hood hashing | 2 | 1.125 | 1.1667 | 1.0556 | 1.1111 | 0.0556 | 0.2291 | 1 | 4 | 0 |
| Delete-heavy (30.0% removals) | 0.25 | 0.1935 | Linear probing | 2 | 1.125 | 1.1667 | 1.0556 | 1.3333 | 0.0556 | 0.2291 | 1 | 4 | 0 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3548 | Robin Hood hashing | 5 | 1.2083 | 1.0667 | 1.1818 | 1.3939 | 0.1818 | 0.3857 | 1 | 3 | 0.6667 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3548 | Linear probing | 5 | 1.2083 | 1.0667 | 1.1818 | 1.5455 | 0.1818 | 0.4576 | 2 | 3 | 0 |
| Delete-heavy (30.0% removals) | 0.75 | 0.5161 | Robin Hood hashing | 7 | 1.8986 | 1.619 | 1.4375 | 1.5833 | 0.4375 | 0.8141 | 4 | 6 | 6.6667 |
| Delete-heavy (30.0% removals) | 0.75 | 0.5161 | Linear probing | 7 | 1.8986 | 1.619 | 1.4375 | 2.1667 | 0.4375 | 0.9554 | 4 | 6 | 0 |

## Probe-distance histograms

Counts are aggregated across deterministic trials so the variance story is visible without digging through the raw CSV/JSON exports; for delete-heavy runs, the histograms are captured after the deterministic removal pass.

### Fill-only

#### Requested load factor 0.25 → remaining 0.2581

8 starting entries per trial; 8 remain after the workload across 3 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 21 (87.5%) ██████████ | 21 (87.5%) ██████████ |
| 1 | 3 (12.5%) ██ | 3 (12.5%) ██ |

#### Requested load factor 0.5 → remaining 0.5161

16 starting entries per trial; 16 remain after the workload across 3 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 38 (79.2%) ██████████ | 40 (83.3%) ██████████ |
| 1 | 10 (20.8%) ██ | 6 (12.5%) ██ |
| 2 | 0 (0.0%) | 2 (4.2%) █ |

#### Requested load factor 0.75 → remaining 0.7419

23 starting entries per trial; 23 remain after the workload across 3 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 31 (44.9%) █████ | 45 (65.2%) ████████ |
| 1 | 21 (30.4%) ████ | 9 (13.0%) ██ |
| 2 | 13 (18.8%) ██ | 5 (7.2%) █ |
| 3 | 2 (2.9%) █ | 4 (5.8%) █ |
| 4 | 1 (1.5%) █ | 2 (2.9%) █ |
| 5 | 1 (1.5%) █ | 2 (2.9%) █ |
| 6 | 0 (0.0%) | 1 (1.5%) █ |
| 7 | 0 (0.0%) | 1 (1.5%) █ |

### Delete-heavy (30.0% removals)

#### Requested load factor 0.25 → remaining 0.1935

8 starting entries per trial; 6 remain after the workload across 3 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 17 (94.4%) ███████████ | 17 (94.4%) ███████████ |
| 1 | 1 (5.6%) █ | 1 (5.6%) █ |

#### Requested load factor 0.5 → remaining 0.3548

16 starting entries per trial; 11 remain after the workload across 3 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 27 (81.8%) ██████████ | 28 (84.9%) ██████████ |
| 1 | 6 (18.2%) ██ | 4 (12.1%) █ |
| 2 | 0 (0.0%) | 1 (3.0%) █ |

#### Requested load factor 0.75 → remaining 0.5161

23 starting entries per trial; 16 remain after the workload across 3 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 33 (68.8%) ████████ | 37 (77.1%) █████████ |
| 1 | 12 (25.0%) ███ | 6 (12.5%) ██ |
| 2 | 1 (2.1%) █ | 1 (2.1%) █ |
| 3 | 1 (2.1%) █ | 3 (6.2%) █ |
| 4 | 1 (2.1%) █ | 1 (2.1%) █ |

## Unsuccessful-lookup histograms

Counts are aggregated across deterministic trials after each workload finishes, so failed-search cost is visible alongside the resident probe-distance story.

### Fill-only

#### Requested load factor 0.25 → remaining 0.2581

8 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 8 resident entries across 3 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 17 (70.8%) ████████ | 20 (83.3%) ██████████ |
| 2 | 5 (20.8%) ██ | 3 (12.5%) ██ |
| 3 | 2 (8.3%) █ | 1 (4.2%) █ |

#### Requested load factor 0.5 → remaining 0.5161

16 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 16 resident entries across 3 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 20 (41.7%) █████ | 20 (41.7%) █████ |
| 2 | 19 (39.6%) █████ | 12 (25.0%) ███ |
| 3 | 9 (18.8%) ██ | 6 (12.5%) ██ |
| 4 | 0 (0.0%) | 7 (14.6%) ██ |
| 5 | 0 (0.0%) | 1 (2.1%) █ |
| 6 | 0 (0.0%) | 2 (4.2%) █ |

#### Requested load factor 0.75 → remaining 0.7419

23 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 23 resident entries across 3 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 20 (29.0%) ███ | 26 (37.7%) █████ |
| 2 | 17 (24.6%) ███ | 5 (7.2%) █ |
| 3 | 20 (29.0%) ███ | 13 (18.8%) ██ |
| 4 | 10 (14.5%) ██ | 0 (0.0%) |
| 5 | 1 (1.5%) █ | 7 (10.1%) █ |
| 6 | 1 (1.5%) █ | 4 (5.8%) █ |
| 7 | 0 (0.0%) | 3 (4.3%) █ |
| 8 | 0 (0.0%) | 4 (5.8%) █ |
| 10 | 0 (0.0%) | 1 (1.5%) █ |
| 11 | 0 (0.0%) | 1 (1.5%) █ |
| 12 | 0 (0.0%) | 1 (1.5%) █ |
| 14 | 0 (0.0%) | 2 (2.9%) █ |
| 15 | 0 (0.0%) | 2 (2.9%) █ |

### Delete-heavy (30.0% removals)

#### Requested load factor 0.25 → remaining 0.1935

6 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 6 resident entries across 3 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 16 (88.9%) ███████████ | 15 (83.3%) ██████████ |
| 2 | 2 (11.1%) █ | 1 (5.6%) █ |
| 3 | 0 (0.0%) | 1 (5.6%) █ |
| 4 | 0 (0.0%) | 1 (5.6%) █ |

#### Requested load factor 0.5 → remaining 0.3548

11 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 11 resident entries across 3 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 23 (69.7%) ████████ | 18 (54.5%) ███████ |
| 2 | 7 (21.2%) ███ | 13 (39.4%) █████ |
| 3 | 3 (9.1%) █ | 1 (3.0%) █ |
| 4 | 0 (0.0%) | 1 (3.0%) █ |

#### Requested load factor 0.75 → remaining 0.5161

16 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 16 resident entries across 3 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 26 (54.2%) ███████ | 24 (50.0%) ██████ |
| 2 | 18 (37.5%) ████ | 7 (14.6%) ██ |
| 3 | 3 (6.2%) █ | 8 (16.7%) ██ |
| 4 | 0 (0.0%) | 4 (8.3%) █ |
| 5 | 1 (2.1%) █ | 4 (8.3%) █ |
| 6 | 0 (0.0%) | 1 (2.1%) █ |


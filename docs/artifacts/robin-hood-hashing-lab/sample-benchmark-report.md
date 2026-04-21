# Robin Hood hashing benchmark comparison with delete-heavy workloads

Deterministic benchmark report comparing Robin Hood hashing against a linear-probing baseline, with probe-distance histograms that make dispersion visible at a glance. It also includes a delete-heavy workload that removes 30.0% of keys before the final lookup + histogram pass, so post-removal clustering is visible too.

- Capacity: 31
- Trials per workload/load factor: 3
- Strategies: Robin Hood hashing, Linear probing
- Workloads: Fill-only, Delete-heavy (30.0% removals)
- Requested load factors: 0.25, 0.5, 0.75
- Note: requested load factors are rounded to whole entry counts, so the effective fill level can differ slightly from the requested target.

## Headline comparisons

| Workload | Requested load factor | Remaining load factor | Remaining entries | Lookup winner | Lookup delta vs linear | Lower probe-distance stddev | Stddev delta vs linear | Lower delete probes | Delete delta vs linear |
| --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- | ---: |
| Fill-only | 0.25 | 0.2581 | 8 | Tie | 0 | Tie | 0 | — | — |
| Fill-only | 0.5 | 0.5161 | 16 | Tie | 0 | Robin Hood hashing | 0.0922 | — | — |
| Fill-only | 0.75 | 0.7419 | 23 | Tie | 0 | Robin Hood hashing | 0.5469 | — | — |
| Delete-heavy (30.0% removals) | 0.25 | 0.1935 | 6 | Tie | 0 | Tie | 0 | Tie | 0 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3548 | 11 | Tie | 0 | Robin Hood hashing | 0.0719 | Tie | 0 |
| Delete-heavy (30.0% removals) | 0.75 | 0.5161 | 16 | Tie | 0 | Robin Hood hashing | 0.1413 | Tie | 0 |

## Aggregate metrics

| Workload | Requested load factor | Remaining load factor | Strategy | Deleted entries | Avg insert probes | Avg delete probes | Avg successful lookup probes | Avg probe distance | Probe-distance stddev | Max probe distance | Max cluster length | Avg swaps |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fill-only | 0.25 | 0.2581 | Robin Hood hashing | 0 | 1.125 | 0 | 1.125 | 0.125 | 0.3307 | 1 | 5 | 0 |
| Fill-only | 0.25 | 0.2581 | Linear probing | 0 | 1.125 | 0 | 1.125 | 0.125 | 0.3307 | 1 | 5 | 0 |
| Fill-only | 0.5 | 0.5161 | Robin Hood hashing | 0 | 1.2083 | 0 | 1.2083 | 0.2083 | 0.4061 | 1 | 7 | 0.6667 |
| Fill-only | 0.5 | 0.5161 | Linear probing | 0 | 1.2083 | 0 | 1.2083 | 0.2083 | 0.4983 | 2 | 7 | 0 |
| Fill-only | 0.75 | 0.7419 | Robin Hood hashing | 0 | 1.8986 | 0 | 1.8986 | 0.8986 | 1.0515 | 5 | 14 | 6.6667 |
| Fill-only | 0.75 | 0.7419 | Linear probing | 0 | 1.8986 | 0 | 1.8986 | 0.8986 | 1.5984 | 7 | 14 | 0 |
| Delete-heavy (30.0% removals) | 0.25 | 0.1935 | Robin Hood hashing | 2 | 1.125 | 1.1667 | 1.0556 | 0.0556 | 0.2291 | 1 | 4 | 0 |
| Delete-heavy (30.0% removals) | 0.25 | 0.1935 | Linear probing | 2 | 1.125 | 1.1667 | 1.0556 | 0.0556 | 0.2291 | 1 | 4 | 0 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3548 | Robin Hood hashing | 5 | 1.2083 | 1.0667 | 1.1818 | 0.1818 | 0.3857 | 1 | 3 | 0.6667 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3548 | Linear probing | 5 | 1.2083 | 1.0667 | 1.1818 | 0.1818 | 0.4576 | 2 | 3 | 0 |
| Delete-heavy (30.0% removals) | 0.75 | 0.5161 | Robin Hood hashing | 7 | 1.8986 | 1.619 | 1.4375 | 0.4375 | 0.8141 | 4 | 6 | 6.6667 |
| Delete-heavy (30.0% removals) | 0.75 | 0.5161 | Linear probing | 7 | 1.8986 | 1.619 | 1.4375 | 0.4375 | 0.9554 | 4 | 6 | 0 |

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


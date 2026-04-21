# Robin Hood hashing benchmark comparison with delete-heavy workloads

Deterministic benchmark report comparing Robin Hood hashing against a linear-probing baseline, with resident probe-distance histograms plus hit/miss lookup percentile callouts that make both dispersion and tail cost visible at a glance. It also includes a delete-heavy workload that removes 30.0% of keys before the final hit/miss lookup + histogram pass, so post-removal clustering is visible too.

- Capacity: 127
- Trials per workload/load factor: 5
- Strategies: Robin Hood hashing, Linear probing
- Workloads: Fill-only, Delete-heavy (30.0% removals)
- Requested load factors: 0.25, 0.5, 0.7, 0.85
- Note: requested load factors are rounded to whole entry counts, so the effective fill level can differ slightly from the requested target.

## Headline comparisons

| Workload | Requested load factor | Remaining load factor | Remaining entries | Successful lookup winner | Success delta vs linear | Unsuccessful lookup winner | Miss delta vs linear | Lower probe-distance stddev | Stddev delta vs linear | Lower delete probes | Delete delta vs linear |
| --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- | ---: | --- | ---: |
| Fill-only | 0.25 | 0.252 | 32 | Tie | 0 | Robin Hood hashing | 0.0812 | Robin Hood hashing | 0.0927 | — | — |
| Fill-only | 0.5 | 0.5039 | 64 | Tie | 0 | Robin Hood hashing | 0.7719 | Robin Hood hashing | 0.3354 | — | — |
| Fill-only | 0.7 | 0.7008 | 89 | Tie | 0 | Robin Hood hashing | 2.4449 | Robin Hood hashing | 1.078 | — | — |
| Fill-only | 0.85 | 0.8504 | 108 | Tie | 0 | Robin Hood hashing | 10.3203 | Robin Hood hashing | 4.3104 | — | — |
| Delete-heavy (30.0% removals) | 0.25 | 0.1732 | 22 | Tie | 0 | Robin Hood hashing | 0.091 | Robin Hood hashing | 0.0262 | Linear probing | -0.06 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3543 | 45 | Tie | 0 | Robin Hood hashing | 0.3155 | Robin Hood hashing | 0.0864 | Robin Hood hashing | 0.0527 |
| Delete-heavy (30.0% removals) | 0.7 | 0.4882 | 62 | Tie | 0 | Robin Hood hashing | 0.8259 | Robin Hood hashing | 0.3074 | Linear probing | -0.1037 |
| Delete-heavy (30.0% removals) | 0.85 | 0.5984 | 76 | Tie | 0 | Robin Hood hashing | 1.2079 | Robin Hood hashing | 0.5856 | Robin Hood hashing | 0.7125 |

## Lookup percentile callouts

These side-by-side lookup summaries make hit and miss tails readable without scanning the full histograms.

| Workload | Requested load factor | Remaining load factor | Strategy | Successful lookups avg / p50 / p95 / max | Unsuccessful lookups avg / p50 / p95 / max |
| --- | ---: | ---: | --- | --- | --- |
| Fill-only | 0.25 | 0.252 | Robin Hood hashing | 1.1938 / 1 / 2 / 3 | 1.325 / 1 / 3 / 3 |
| Fill-only | 0.25 | 0.252 | Linear probing | 1.1938 / 1 / 2 / 4 | 1.4062 / 1 / 3 / 5 |
| Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 1.5469 / 1 / 3 / 5 | 1.7906 / 2 / 3 / 5 |
| Fill-only | 0.5 | 0.5039 | Linear probing | 1.5469 / 1 / 3 / 10 | 2.5625 / 2 / 8 / 12 |
| Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 1.9326 / 2 / 4 / 6 | 2.3596 / 2 / 5 / 7 |
| Fill-only | 0.7 | 0.7008 | Linear probing | 1.9326 / 1 / 6 / 18 | 4.8045 / 3 / 16 / 24 |
| Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 3.3148 / 3 / 8 / 12 | 3.7167 / 3 / 9 / 13 |
| Fill-only | 0.85 | 0.8504 | Linear probing | 3.3148 / 1 / 13 / 69 | 14.037 / 7 / 50 / 73 |
| Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 1.1273 / 1 / 2 / 2 | 1.1545 / 1 / 2 / 3 |
| Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 1.1273 / 1 / 2 / 3 | 1.2455 / 1 / 2 / 3 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 1.2622 / 1 / 2 / 4 | 1.4089 / 1 / 3 / 4 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 1.2622 / 1 / 3 / 4 | 1.7244 / 1 / 4 / 8 |
| Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 1.4097 / 1 / 3 / 4 | 1.6806 / 1 / 4 / 5 |
| Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 1.4097 / 1 / 3 / 8 | 2.5065 / 1 / 8 / 16 |
| Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 1.6395 / 1 / 3 / 6 | 1.9842 / 2 / 4 / 6 |
| Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 1.6395 / 1 / 4 / 14 | 3.1921 / 2 / 11 / 20 |

Positive p95 deltas mean Robin Hood hashing had the shorter lookup tail than linear probing for that slice.

| Workload | Requested load factor | Lower hit p95 | Hit p95 delta vs linear | Lower miss p95 | Miss p95 delta vs linear |
| --- | ---: | --- | ---: | --- | ---: |
| Fill-only | 0.25 | Tie | 0 | Tie | 0 |
| Fill-only | 0.5 | Tie | 0 | Robin Hood hashing | 5 |
| Fill-only | 0.7 | Robin Hood hashing | 2 | Robin Hood hashing | 11 |
| Fill-only | 0.85 | Robin Hood hashing | 5 | Robin Hood hashing | 41 |
| Delete-heavy (30.0% removals) | 0.25 | Tie | 0 | Tie | 0 |
| Delete-heavy (30.0% removals) | 0.5 | Robin Hood hashing | 1 | Robin Hood hashing | 1 |
| Delete-heavy (30.0% removals) | 0.7 | Tie | 0 | Robin Hood hashing | 4 |
| Delete-heavy (30.0% removals) | 0.85 | Robin Hood hashing | 1 | Robin Hood hashing | 7 |

## Aggregate metrics

| Workload | Requested load factor | Remaining load factor | Strategy | Deleted entries | Avg insert probes | Avg delete probes | Avg successful lookup probes | Avg unsuccessful lookup probes | Avg probe distance | Probe-distance stddev | Max probe distance | Max cluster length | Avg swaps |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fill-only | 0.25 | 0.252 | Robin Hood hashing | 0 | 1.1938 | 0 | 1.1938 | 1.325 | 0.1938 | 0.4257 | 2 | 5 | 1 |
| Fill-only | 0.25 | 0.252 | Linear probing | 0 | 1.1938 | 0 | 1.1938 | 1.4062 | 0.1938 | 0.5184 | 3 | 5 | 0 |
| Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 0 | 1.5469 | 0 | 1.5469 | 1.7906 | 0.5469 | 0.8202 | 4 | 11 | 9 |
| Fill-only | 0.5 | 0.5039 | Linear probing | 0 | 1.5469 | 0 | 1.5469 | 2.5625 | 0.5469 | 1.1556 | 9 | 11 | 0 |
| Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 0 | 1.9326 | 0 | 1.9326 | 2.3596 | 0.9326 | 1.1475 | 5 | 24 | 35.6 |
| Fill-only | 0.7 | 0.7008 | Linear probing | 0 | 1.9326 | 0 | 1.9326 | 4.8045 | 0.9326 | 2.2255 | 17 | 24 | 0 |
| Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 0 | 3.3148 | 0 | 3.3148 | 3.7167 | 2.3148 | 2.3176 | 11 | 72 | 127.8 |
| Fill-only | 0.85 | 0.8504 | Linear probing | 0 | 3.3148 | 0 | 3.3148 | 14.037 | 2.3148 | 6.628 | 68 | 72 | 0 |
| Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 10 | 1.1938 | 1.16 | 1.1273 | 1.1545 | 0.1273 | 0.3333 | 1 | 4 | 1 |
| Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 10 | 1.1938 | 1.1 | 1.1273 | 1.2455 | 0.1273 | 0.3595 | 2 | 4 | 0 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 19 | 1.5469 | 1.4526 | 1.2622 | 1.4089 | 0.2622 | 0.5229 | 3 | 7 | 9 |
| Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 19 | 1.5469 | 1.5053 | 1.2622 | 1.7244 | 0.2622 | 0.6093 | 3 | 7 | 0 |
| Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 27 | 1.9326 | 1.5481 | 1.4097 | 1.6806 | 0.4097 | 0.6647 | 3 | 16 | 35.6 |
| Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 27 | 1.9326 | 1.4444 | 1.4097 | 2.5065 | 0.4097 | 0.9721 | 7 | 16 | 0 |
| Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 32 | 3.3148 | 2.25 | 1.6395 | 1.9842 | 0.6395 | 0.9026 | 5 | 20 | 127.8 |
| Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 32 | 3.3148 | 2.9625 | 1.6395 | 3.1921 | 0.6395 | 1.4882 | 13 | 20 | 0 |

## Probe-distance histograms

Counts are aggregated across deterministic trials so the variance story is visible without digging through the raw CSV/JSON exports; for delete-heavy runs, the histograms are captured after the deterministic removal pass.

### Fill-only

#### Requested load factor 0.25 → remaining 0.252

32 starting entries per trial; 32 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 131 (81.9%) ██████████ | 136 (85.0%) ██████████ |
| 1 | 27 (16.9%) ██ | 19 (11.9%) █ |
| 2 | 2 (1.2%) █ | 3 (1.9%) █ |
| 3 | 0 (0.0%) | 2 (1.2%) █ |

#### Requested load factor 0.5 → remaining 0.5039

64 starting entries per trial; 64 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 196 (61.3%) ███████ | 225 (70.3%) ████████ |
| 1 | 87 (27.2%) ███ | 57 (17.8%) ██ |
| 2 | 26 (8.1%) █ | 22 (6.9%) █ |
| 3 | 8 (2.5%) █ | 3 (0.9%) █ |
| 4 | 3 (0.9%) █ | 7 (2.2%) █ |
| 5 | 0 (0.0%) | 2 (0.6%) █ |
| 6 | 0 (0.0%) | 3 (0.9%) █ |
| 9 | 0 (0.0%) | 1 (0.3%) █ |

#### Requested load factor 0.7 → remaining 0.7008

89 starting entries per trial; 89 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 214 (48.1%) ██████ | 305 (68.5%) ████████ |
| 1 | 119 (26.7%) ███ | 59 (13.3%) ██ |
| 2 | 61 (13.7%) ██ | 32 (7.2%) █ |
| 3 | 32 (7.2%) █ | 16 (3.6%) █ |
| 4 | 17 (3.8%) █ | 9 (2.0%) █ |
| 5 | 2 (0.4%) █ | 7 (1.6%) █ |
| 6 | 0 (0.0%) | 1 (0.2%) █ |
| 7 | 0 (0.0%) | 2 (0.4%) █ |
| 8 | 0 (0.0%) | 4 (0.9%) █ |
| 9 | 0 (0.0%) | 2 (0.4%) █ |
| 10 | 0 (0.0%) | 2 (0.4%) █ |
| 11 | 0 (0.0%) | 2 (0.4%) █ |
| 12 | 0 (0.0%) | 1 (0.2%) █ |
| 15 | 0 (0.0%) | 1 (0.2%) █ |
| 17 | 0 (0.0%) | 2 (0.4%) █ |

#### Requested load factor 0.85 → remaining 0.8504

108 starting entries per trial; 108 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 135 (25.0%) ███ | 324 (60.0%) ███████ |
| 1 | 114 (21.1%) ███ | 73 (13.5%) ██ |
| 2 | 74 (13.7%) ██ | 32 (5.9%) █ |
| 3 | 94 (17.4%) ██ | 24 (4.4%) █ |
| 4 | 50 (9.3%) █ | 19 (3.5%) █ |
| 5 | 23 (4.3%) █ | 12 (2.2%) █ |
| 6 | 12 (2.2%) █ | 10 (1.8%) █ |
| 7 | 11 (2.0%) █ | 4 (0.7%) █ |
| 8 | 10 (1.8%) █ | 6 (1.1%) █ |
| 9 | 10 (1.8%) █ | 6 (1.1%) █ |
| 10 | 5 (0.9%) █ | 0 (0.0%) |
| 11 | 2 (0.4%) █ | 2 (0.4%) █ |
| 12 | 0 (0.0%) | 5 (0.9%) █ |
| 13 | 0 (0.0%) | 3 (0.6%) █ |
| 14 | 0 (0.0%) | 2 (0.4%) █ |
| 15 | 0 (0.0%) | 1 (0.2%) █ |
| 16 | 0 (0.0%) | 1 (0.2%) █ |
| 17 | 0 (0.0%) | 1 (0.2%) █ |
| 18 | 0 (0.0%) | 1 (0.2%) █ |
| 19 | 0 (0.0%) | 1 (0.2%) █ |
| 20 | 0 (0.0%) | 1 (0.2%) █ |
| 22 | 0 (0.0%) | 1 (0.2%) █ |
| 26 | 0 (0.0%) | 1 (0.2%) █ |
| 27 | 0 (0.0%) | 1 (0.2%) █ |
| 28 | 0 (0.0%) | 1 (0.2%) █ |
| 30 | 0 (0.0%) | 2 (0.4%) █ |
| 33 | 0 (0.0%) | 1 (0.2%) █ |
| 37 | 0 (0.0%) | 1 (0.2%) █ |
| 40 | 0 (0.0%) | 1 (0.2%) █ |
| 53 | 0 (0.0%) | 1 (0.2%) █ |
| 67 | 0 (0.0%) | 1 (0.2%) █ |
| 68 | 0 (0.0%) | 1 (0.2%) █ |

### Delete-heavy (30.0% removals)

#### Requested load factor 0.25 → remaining 0.1732

32 starting entries per trial; 22 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 96 (87.3%) ██████████ | 97 (88.2%) ███████████ |
| 1 | 14 (12.7%) ██ | 12 (10.9%) █ |
| 2 | 0 (0.0%) | 1 (0.9%) █ |

#### Requested load factor 0.5 → remaining 0.3543

64 starting entries per trial; 45 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 174 (77.3%) █████████ | 183 (81.3%) ██████████ |
| 1 | 44 (19.6%) ██ | 28 (12.4%) █ |
| 2 | 6 (2.7%) █ | 11 (4.9%) █ |
| 3 | 1 (0.4%) █ | 3 (1.3%) █ |

#### Requested load factor 0.7 → remaining 0.4882

89 starting entries per trial; 62 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 211 (68.1%) ████████ | 243 (78.4%) █████████ |
| 1 | 74 (23.9%) ███ | 34 (11.0%) █ |
| 2 | 22 (7.1%) █ | 19 (6.1%) █ |
| 3 | 3 (1.0%) █ | 7 (2.3%) █ |
| 4 | 0 (0.0%) | 3 (1.0%) █ |
| 5 | 0 (0.0%) | 3 (1.0%) █ |
| 7 | 0 (0.0%) | 1 (0.3%) █ |

#### Requested load factor 0.85 → remaining 0.5984

108 starting entries per trial; 76 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 215 (56.6%) ███████ | 273 (71.8%) █████████ |
| 1 | 112 (29.5%) ████ | 56 (14.7%) ██ |
| 2 | 35 (9.2%) █ | 19 (5.0%) █ |
| 3 | 12 (3.2%) █ | 14 (3.7%) █ |
| 4 | 5 (1.3%) █ | 6 (1.6%) █ |
| 5 | 1 (0.3%) █ | 4 (1.1%) █ |
| 6 | 0 (0.0%) | 4 (1.1%) █ |
| 7 | 0 (0.0%) | 1 (0.3%) █ |
| 9 | 0 (0.0%) | 1 (0.3%) █ |
| 10 | 0 (0.0%) | 1 (0.3%) █ |
| 13 | 0 (0.0%) | 1 (0.3%) █ |

## Unsuccessful-lookup histograms

Counts are aggregated across deterministic trials after each workload finishes, so failed-search cost is visible alongside the resident probe-distance story.

### Fill-only

#### Requested load factor 0.25 → remaining 0.252

32 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 32 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 117 (73.1%) █████████ | 116 (72.5%) █████████ |
| 2 | 34 (21.2%) ███ | 32 (20.0%) ██ |
| 3 | 9 (5.6%) █ | 6 (3.8%) █ |
| 4 | 0 (0.0%) | 3 (1.9%) █ |
| 5 | 0 (0.0%) | 3 (1.9%) █ |

#### Requested load factor 0.5 → remaining 0.5039

64 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 64 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 153 (47.8%) ██████ | 158 (49.4%) ██████ |
| 2 | 99 (30.9%) ████ | 61 (19.1%) ██ |
| 3 | 53 (16.6%) ██ | 31 (9.7%) █ |
| 4 | 12 (3.8%) █ | 19 (5.9%) █ |
| 5 | 3 (0.9%) █ | 14 (4.4%) █ |
| 6 | 0 (0.0%) | 8 (2.5%) █ |
| 7 | 0 (0.0%) | 9 (2.8%) █ |
| 8 | 0 (0.0%) | 8 (2.5%) █ |
| 9 | 0 (0.0%) | 2 (0.6%) █ |
| 10 | 0 (0.0%) | 4 (1.2%) █ |
| 11 | 0 (0.0%) | 4 (1.2%) █ |
| 12 | 0 (0.0%) | 2 (0.6%) █ |

#### Requested load factor 0.7 → remaining 0.7008

89 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 89 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 138 (31.0%) ████ | 122 (27.4%) ███ |
| 2 | 150 (33.7%) ████ | 76 (17.1%) ██ |
| 3 | 73 (16.4%) ██ | 55 (12.4%) █ |
| 4 | 40 (9.0%) █ | 41 (9.2%) █ |
| 5 | 33 (7.4%) █ | 22 (4.9%) █ |
| 6 | 9 (2.0%) █ | 30 (6.7%) █ |
| 7 | 2 (0.4%) █ | 12 (2.7%) █ |
| 8 | 0 (0.0%) | 9 (2.0%) █ |
| 9 | 0 (0.0%) | 14 (3.1%) █ |
| 10 | 0 (0.0%) | 5 (1.1%) █ |
| 11 | 0 (0.0%) | 6 (1.4%) █ |
| 12 | 0 (0.0%) | 8 (1.8%) █ |
| 13 | 0 (0.0%) | 7 (1.6%) █ |
| 14 | 0 (0.0%) | 8 (1.8%) █ |
| 15 | 0 (0.0%) | 7 (1.6%) █ |
| 16 | 0 (0.0%) | 7 (1.6%) █ |
| 17 | 0 (0.0%) | 1 (0.2%) █ |
| 18 | 0 (0.0%) | 4 (0.9%) █ |
| 19 | 0 (0.0%) | 1 (0.2%) █ |
| 20 | 0 (0.0%) | 2 (0.4%) █ |
| 21 | 0 (0.0%) | 1 (0.2%) █ |
| 22 | 0 (0.0%) | 1 (0.2%) █ |
| 23 | 0 (0.0%) | 4 (0.9%) █ |
| 24 | 0 (0.0%) | 2 (0.4%) █ |

#### Requested load factor 0.85 → remaining 0.8504

108 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 108 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 92 (17.0%) ██ | 88 (16.3%) ██ |
| 2 | 115 (21.3%) ███ | 54 (10.0%) █ |
| 3 | 89 (16.5%) ██ | 43 (8.0%) █ |
| 4 | 68 (12.6%) ██ | 32 (5.9%) █ |
| 5 | 70 (13.0%) ██ | 19 (3.5%) █ |
| 6 | 46 (8.5%) █ | 15 (2.8%) █ |
| 7 | 24 (4.4%) █ | 20 (3.7%) █ |
| 8 | 8 (1.5%) █ | 18 (3.3%) █ |
| 9 | 10 (1.8%) █ | 11 (2.0%) █ |
| 10 | 6 (1.1%) █ | 17 (3.1%) █ |
| 11 | 7 (1.3%) █ | 15 (2.8%) █ |
| 12 | 4 (0.7%) █ | 12 (2.2%) █ |
| 13 | 1 (0.2%) █ | 16 (3.0%) █ |
| 14 | 0 (0.0%) | 8 (1.5%) █ |
| 15 | 0 (0.0%) | 6 (1.1%) █ |
| 16 | 0 (0.0%) | 6 (1.1%) █ |
| 17 | 0 (0.0%) | 15 (2.8%) █ |
| 18 | 0 (0.0%) | 7 (1.3%) █ |
| 19 | 0 (0.0%) | 7 (1.3%) █ |
| 20 | 0 (0.0%) | 7 (1.3%) █ |
| 21 | 0 (0.0%) | 10 (1.8%) █ |
| 22 | 0 (0.0%) | 2 (0.4%) █ |
| 23 | 0 (0.0%) | 6 (1.1%) █ |
| 24 | 0 (0.0%) | 3 (0.6%) █ |
| 25 | 0 (0.0%) | 3 (0.6%) █ |
| 26 | 0 (0.0%) | 4 (0.7%) █ |
| 27 | 0 (0.0%) | 2 (0.4%) █ |
| 28 | 0 (0.0%) | 1 (0.2%) █ |
| 29 | 0 (0.0%) | 2 (0.4%) █ |
| 30 | 0 (0.0%) | 3 (0.6%) █ |
| 31 | 0 (0.0%) | 3 (0.6%) █ |
| 32 | 0 (0.0%) | 3 (0.6%) █ |
| 33 | 0 (0.0%) | 1 (0.2%) █ |
| 34 | 0 (0.0%) | 6 (1.1%) █ |
| 35 | 0 (0.0%) | 4 (0.7%) █ |
| 36 | 0 (0.0%) | 8 (1.5%) █ |
| 37 | 0 (0.0%) | 3 (0.6%) █ |
| 38 | 0 (0.0%) | 2 (0.4%) █ |
| 39 | 0 (0.0%) | 3 (0.6%) █ |
| 40 | 0 (0.0%) | 4 (0.7%) █ |
| 41 | 0 (0.0%) | 1 (0.2%) █ |
| 42 | 0 (0.0%) | 1 (0.2%) █ |
| 43 | 0 (0.0%) | 3 (0.6%) █ |
| 44 | 0 (0.0%) | 3 (0.6%) █ |
| 45 | 0 (0.0%) | 1 (0.2%) █ |
| 46 | 0 (0.0%) | 4 (0.7%) █ |
| 47 | 0 (0.0%) | 1 (0.2%) █ |
| 48 | 0 (0.0%) | 5 (0.9%) █ |
| 49 | 0 (0.0%) | 3 (0.6%) █ |
| 50 | 0 (0.0%) | 3 (0.6%) █ |
| 52 | 0 (0.0%) | 1 (0.2%) █ |
| 53 | 0 (0.0%) | 3 (0.6%) █ |
| 54 | 0 (0.0%) | 1 (0.2%) █ |
| 55 | 0 (0.0%) | 3 (0.6%) █ |
| 57 | 0 (0.0%) | 2 (0.4%) █ |
| 58 | 0 (0.0%) | 2 (0.4%) █ |
| 59 | 0 (0.0%) | 3 (0.6%) █ |
| 60 | 0 (0.0%) | 2 (0.4%) █ |
| 62 | 0 (0.0%) | 1 (0.2%) █ |
| 64 | 0 (0.0%) | 2 (0.4%) █ |
| 67 | 0 (0.0%) | 1 (0.2%) █ |
| 70 | 0 (0.0%) | 1 (0.2%) █ |
| 71 | 0 (0.0%) | 2 (0.4%) █ |
| 73 | 0 (0.0%) | 2 (0.4%) █ |

### Delete-heavy (30.0% removals)

#### Requested load factor 0.25 → remaining 0.1732

22 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 22 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 95 (86.4%) ██████████ | 86 (78.2%) █████████ |
| 2 | 13 (11.8%) █ | 21 (19.1%) ██ |
| 3 | 2 (1.8%) █ | 3 (2.7%) █ |

#### Requested load factor 0.5 → remaining 0.3543

45 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 45 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 146 (64.9%) ████████ | 131 (58.2%) ███████ |
| 2 | 67 (29.8%) ████ | 55 (24.4%) ███ |
| 3 | 11 (4.9%) █ | 23 (10.2%) █ |
| 4 | 1 (0.4%) █ | 9 (4.0%) █ |
| 5 | 0 (0.0%) | 3 (1.3%) █ |
| 6 | 0 (0.0%) | 2 (0.9%) █ |
| 7 | 0 (0.0%) | 1 (0.4%) █ |
| 8 | 0 (0.0%) | 1 (0.4%) █ |

#### Requested load factor 0.7 → remaining 0.4882

62 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 62 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 168 (54.2%) ███████ | 156 (50.3%) ██████ |
| 2 | 94 (30.3%) ████ | 58 (18.7%) ██ |
| 3 | 32 (10.3%) █ | 32 (10.3%) █ |
| 4 | 11 (3.5%) █ | 24 (7.7%) █ |
| 5 | 5 (1.6%) █ | 13 (4.2%) █ |
| 6 | 0 (0.0%) | 10 (3.2%) █ |
| 7 | 0 (0.0%) | 1 (0.3%) █ |
| 8 | 0 (0.0%) | 2 (0.7%) █ |
| 9 | 0 (0.0%) | 1 (0.3%) █ |
| 10 | 0 (0.0%) | 5 (1.6%) █ |
| 11 | 0 (0.0%) | 2 (0.7%) █ |
| 13 | 0 (0.0%) | 3 (1.0%) █ |
| 14 | 0 (0.0%) | 1 (0.3%) █ |
| 15 | 0 (0.0%) | 1 (0.3%) █ |
| 16 | 0 (0.0%) | 1 (0.3%) █ |

#### Requested load factor 0.85 → remaining 0.5984

76 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 76 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 159 (41.8%) █████ | 153 (40.3%) █████ |
| 2 | 121 (31.8%) ████ | 72 (18.9%) ██ |
| 3 | 62 (16.3%) ██ | 49 (12.9%) ██ |
| 4 | 25 (6.6%) █ | 34 (8.9%) █ |
| 5 | 11 (2.9%) █ | 15 (4.0%) █ |
| 6 | 2 (0.5%) █ | 9 (2.4%) █ |
| 7 | 0 (0.0%) | 13 (3.4%) █ |
| 8 | 0 (0.0%) | 7 (1.8%) █ |
| 9 | 0 (0.0%) | 6 (1.6%) █ |
| 10 | 0 (0.0%) | 2 (0.5%) █ |
| 11 | 0 (0.0%) | 3 (0.8%) █ |
| 12 | 0 (0.0%) | 4 (1.1%) █ |
| 13 | 0 (0.0%) | 3 (0.8%) █ |
| 14 | 0 (0.0%) | 1 (0.3%) █ |
| 15 | 0 (0.0%) | 2 (0.5%) █ |
| 16 | 0 (0.0%) | 3 (0.8%) █ |
| 17 | 0 (0.0%) | 3 (0.8%) █ |
| 20 | 0 (0.0%) | 1 (0.3%) █ |


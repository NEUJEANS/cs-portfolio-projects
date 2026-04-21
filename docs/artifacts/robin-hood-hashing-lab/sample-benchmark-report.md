# Robin Hood hashing benchmark comparison with delete-heavy workloads

Deterministic benchmark report comparing Robin Hood hashing against a linear-probing baseline, with resident probe-distance histograms plus hit/miss lookup percentile callouts that make both dispersion and tail cost visible at a glance. It also includes a delete-heavy workload that removes 30.0% of keys before the final hit/miss lookup + histogram pass, so post-removal clustering is visible too. It also compares Random string IDs and Sequential integer IDs, so the same workloads can be narrated as longer text-like IDs versus compact numeric IDs while keeping the snapshot format string-only.

- Capacity: 127
- Trials per workload/load factor: 5
- Key profiles: Random string IDs, Sequential integer IDs
- Strategies: Robin Hood hashing, Linear probing
- Workloads: Fill-only, Delete-heavy (30.0% removals)
- Requested load factors: 0.25, 0.5, 0.7, 0.85
- Note: requested load factors are rounded to whole entry counts, so the effective fill level can differ slightly from the requested target.

## Headline comparisons

| Key profile | Workload | Requested load factor | Remaining load factor | Remaining entries | Successful lookup winner | Success delta vs linear | Unsuccessful lookup winner | Miss delta vs linear | Lower probe-distance stddev | Stddev delta vs linear | Lower delete probes | Delete delta vs linear |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- | ---: | --- | ---: |
| Random string IDs | Fill-only | 0.25 | 0.252 | 32 | Tie | 0 | Robin Hood hashing | 0.1375 | Robin Hood hashing | 0.0803 | — | — |
| Random string IDs | Fill-only | 0.5 | 0.5039 | 64 | Tie | 0 | Robin Hood hashing | 0.3906 | Robin Hood hashing | 0.2529 | — | — |
| Random string IDs | Fill-only | 0.7 | 0.7008 | 89 | Tie | 0 | Robin Hood hashing | 2.9393 | Robin Hood hashing | 0.8624 | — | — |
| Random string IDs | Fill-only | 0.85 | 0.8504 | 108 | Tie | 0 | Robin Hood hashing | 13.4074 | Robin Hood hashing | 3.415 | — | — |
| Random string IDs | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | 22 | Tie | 0 | Robin Hood hashing | 0.0636 | Robin Hood hashing | 0.0275 | Robin Hood hashing | 0.04 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | 45 | Tie | 0 | Robin Hood hashing | 0.0755 | Robin Hood hashing | 0.0743 | Linear probing | -0.021 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | 62 | Tie | 0 | Robin Hood hashing | 0.4742 | Robin Hood hashing | 0.2638 | Linear probing | -0.2222 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | 76 | Tie | 0 | Robin Hood hashing | 1.4895 | Robin Hood hashing | 0.5527 | Linear probing | -0.1 |
| Sequential integer IDs | Fill-only | 0.25 | 0.252 | 32 | Tie | 0 | Robin Hood hashing | 0.0688 | Robin Hood hashing | 0.1238 | — | — |
| Sequential integer IDs | Fill-only | 0.5 | 0.5039 | 64 | Tie | 0 | Robin Hood hashing | 0.7125 | Robin Hood hashing | 0.2957 | — | — |
| Sequential integer IDs | Fill-only | 0.7 | 0.7008 | 89 | Tie | 0 | Robin Hood hashing | 2.5281 | Robin Hood hashing | 1.0857 | — | — |
| Sequential integer IDs | Fill-only | 0.85 | 0.8504 | 108 | Tie | 0 | Robin Hood hashing | 9.7019 | Robin Hood hashing | 3.1178 | — | — |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | 22 | Tie | 0 | Tie | 0 | Robin Hood hashing | 0.1168 | Linear probing | -0.04 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | 45 | Tie | 0 | Robin Hood hashing | 0.4045 | Robin Hood hashing | 0.1697 | Tie | 0 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | 62 | Tie | 0 | Robin Hood hashing | 0.771 | Robin Hood hashing | 0.5218 | Tie | 0 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | 76 | Tie | 0 | Robin Hood hashing | 1.2658 | Robin Hood hashing | 0.5785 | Robin Hood hashing | 0.1938 |

## Lookup percentile callouts

These side-by-side lookup summaries make hit and miss tails readable without scanning the full histograms.

| Key profile | Workload | Requested load factor | Remaining load factor | Strategy | Successful lookups avg / p50 / p95 / max | Unsuccessful lookups avg / p50 / p95 / max |
| --- | --- | ---: | ---: | --- | --- | --- |
| Random string IDs | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 1.2125 / 1 / 2 / 3 | 1.2875 / 1 / 2 / 4 |
| Random string IDs | Fill-only | 0.25 | 0.252 | Linear probing | 1.2125 / 1 / 3 / 5 | 1.425 / 1 / 3 / 9 |
| Random string IDs | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 1.3781 / 1 / 3 / 4 | 1.7688 / 2 / 3 / 5 |
| Random string IDs | Fill-only | 0.5 | 0.5039 | Linear probing | 1.3781 / 1 / 3 / 8 | 2.1594 / 1 / 6 / 10 |
| Random string IDs | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 1.8944 / 2 / 4 / 5 | 2.3551 / 2 / 5 / 6 |
| Random string IDs | Fill-only | 0.7 | 0.7008 | Linear probing | 1.8944 / 1 / 6 / 16 | 5.2944 / 4 / 15 / 22 |
| Random string IDs | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 3.1611 / 3 / 7 / 10 | 3.6704 / 3 / 7 / 11 |
| Random string IDs | Fill-only | 0.85 | 0.8504 | Linear probing | 3.1611 / 1 / 13 / 59 | 17.0778 / 10 / 54 / 79 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 1.0909 / 1 / 2 / 3 | 1.2091 / 1 / 2 / 4 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 1.0909 / 1 / 2 / 3 | 1.2727 / 1 / 3 / 5 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 1.2356 / 1 / 2 / 3 | 1.4889 / 1 / 3 / 4 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 1.2356 / 1 / 2 / 4 | 1.5644 / 1 / 4 / 6 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 1.4355 / 1 / 3 / 4 | 1.6452 / 1 / 3 / 4 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 1.4355 / 1 / 3 / 6 | 2.1194 / 1 / 6 / 11 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 1.6921 / 1 / 4 / 6 | 1.9816 / 2 / 4 / 6 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 1.6921 / 1 / 4 / 12 | 3.4711 / 2 / 11 / 20 |
| Sequential integer IDs | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 1.2563 / 1 / 2 / 5 | 1.2437 / 1 / 2 / 6 |
| Sequential integer IDs | Fill-only | 0.25 | 0.252 | Linear probing | 1.2563 / 1 / 2 / 7 | 1.3125 / 1 / 3 / 4 |
| Sequential integer IDs | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 1.4094 / 1 / 3 / 4 | 1.7031 / 1 / 3 / 4 |
| Sequential integer IDs | Fill-only | 0.5 | 0.5039 | Linear probing | 1.4094 / 1 / 4 / 6 | 2.4156 / 2 / 8 / 11 |
| Sequential integer IDs | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 2.0292 / 2 / 5 / 7 | 2.3236 / 2 / 5 / 8 |
| Sequential integer IDs | Fill-only | 0.7 | 0.7008 | Linear probing | 2.0292 / 1 / 6 / 19 | 4.8517 / 3 / 16 / 24 |
| Sequential integer IDs | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 2.9667 / 2 / 7 / 11 | 3.5185 / 3 / 8 / 12 |
| Sequential integer IDs | Fill-only | 0.85 | 0.8504 | Linear probing | 2.9667 / 1 / 11 / 59 | 13.2204 / 6 / 54 / 78 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 1.1545 / 1 / 2 / 3 | 1.2636 / 1 / 2 / 4 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 1.1545 / 1 / 2 / 5 | 1.2636 / 1 / 3 / 4 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 1.2711 / 1 / 2 / 3 | 1.4133 / 1 / 3 / 4 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 1.2711 / 1 / 3 / 6 | 1.8178 / 1 / 5 / 8 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 1.4387 / 1 / 3 / 5 | 1.5774 / 1 / 3 / 6 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 1.4387 / 1 / 3 / 15 | 2.3484 / 2 / 7 / 18 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 1.6842 / 1 / 4 / 6 | 2.0079 / 2 / 4 / 7 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 1.6842 / 1 / 4 / 15 | 3.2737 / 2 / 10 / 20 |

Positive p95 deltas mean Robin Hood hashing had the shorter lookup tail than linear probing for that slice.

| Key profile | Workload | Requested load factor | Lower hit p95 | Hit p95 delta vs linear | Lower miss p95 | Miss p95 delta vs linear |
| --- | --- | ---: | --- | ---: | --- | ---: |
| Random string IDs | Fill-only | 0.25 | Robin Hood hashing | 1 | Robin Hood hashing | 1 |
| Random string IDs | Fill-only | 0.5 | Tie | 0 | Robin Hood hashing | 3 |
| Random string IDs | Fill-only | 0.7 | Robin Hood hashing | 2 | Robin Hood hashing | 10 |
| Random string IDs | Fill-only | 0.85 | Robin Hood hashing | 6 | Robin Hood hashing | 47 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.25 | Tie | 0 | Robin Hood hashing | 1 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.5 | Tie | 0 | Robin Hood hashing | 1 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.7 | Tie | 0 | Robin Hood hashing | 3 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.85 | Tie | 0 | Robin Hood hashing | 7 |
| Sequential integer IDs | Fill-only | 0.25 | Tie | 0 | Robin Hood hashing | 1 |
| Sequential integer IDs | Fill-only | 0.5 | Robin Hood hashing | 1 | Robin Hood hashing | 5 |
| Sequential integer IDs | Fill-only | 0.7 | Robin Hood hashing | 1 | Robin Hood hashing | 11 |
| Sequential integer IDs | Fill-only | 0.85 | Robin Hood hashing | 4 | Robin Hood hashing | 46 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.25 | Tie | 0 | Robin Hood hashing | 1 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.5 | Robin Hood hashing | 1 | Robin Hood hashing | 2 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.7 | Tie | 0 | Robin Hood hashing | 4 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.85 | Tie | 0 | Robin Hood hashing | 6 |

## Aggregate metrics

| Key profile | Workload | Requested load factor | Remaining load factor | Strategy | Deleted entries | Avg insert probes | Avg delete probes | Avg successful lookup probes | Avg unsuccessful lookup probes | Avg probe distance | Probe-distance stddev | Max probe distance | Max cluster length | Avg swaps |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Random string IDs | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 0 | 1.2125 | 0 | 1.2125 | 1.2875 | 0.2125 | 0.5048 | 2 | 12 | 1.2 |
| Random string IDs | Fill-only | 0.25 | 0.252 | Linear probing | 0 | 1.2125 | 0 | 1.2125 | 1.425 | 0.2125 | 0.5851 | 4 | 12 | 0 |
| Random string IDs | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 0 | 1.3781 | 0 | 1.3781 | 1.7688 | 0.3781 | 0.6644 | 3 | 10 | 5.4 |
| Random string IDs | Fill-only | 0.5 | 0.5039 | Linear probing | 0 | 1.3781 | 0 | 1.3781 | 2.1594 | 0.3781 | 0.9173 | 7 | 10 | 0 |
| Random string IDs | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 0 | 1.8944 | 0 | 1.8944 | 2.3551 | 0.8944 | 0.9785 | 4 | 22 | 32.4 |
| Random string IDs | Fill-only | 0.7 | 0.7008 | Linear probing | 0 | 1.8944 | 0 | 1.8944 | 5.2944 | 0.8944 | 1.8409 | 15 | 22 | 0 |
| Random string IDs | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 0 | 3.1611 | 0 | 3.1611 | 3.6704 | 2.1611 | 1.9355 | 9 | 78 | 106.8 |
| Random string IDs | Fill-only | 0.85 | 0.8504 | Linear probing | 0 | 3.1611 | 0 | 3.1611 | 17.0778 | 2.1611 | 5.3505 | 58 | 78 | 0 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 10 | 1.2125 | 1.18 | 1.0909 | 1.2091 | 0.0909 | 0.3175 | 2 | 4 | 1.2 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 10 | 1.2125 | 1.22 | 1.0909 | 1.2727 | 0.0909 | 0.345 | 2 | 4 | 0 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 19 | 1.3781 | 1.2947 | 1.2356 | 1.4889 | 0.2356 | 0.5012 | 2 | 6 | 5.4 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 19 | 1.3781 | 1.2737 | 1.2356 | 1.5644 | 0.2356 | 0.5755 | 3 | 6 | 0 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 27 | 1.8944 | 1.6074 | 1.4355 | 1.6452 | 0.4355 | 0.6629 | 3 | 10 | 32.4 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 27 | 1.8944 | 1.3852 | 1.4355 | 2.1194 | 0.4355 | 0.9267 | 5 | 10 | 0 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 32 | 3.1611 | 2.2125 | 1.6921 | 1.9816 | 0.6921 | 0.9665 | 5 | 20 | 106.8 |
| Random string IDs | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 32 | 3.1611 | 2.1125 | 1.6921 | 3.4711 | 0.6921 | 1.5192 | 11 | 20 | 0 |
| Sequential integer IDs | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 0 | 1.2563 | 0 | 1.2563 | 1.2437 | 0.2562 | 0.6447 | 4 | 7 | 1.6 |
| Sequential integer IDs | Fill-only | 0.25 | 0.252 | Linear probing | 0 | 1.2563 | 0 | 1.2563 | 1.3125 | 0.2562 | 0.7685 | 6 | 7 | 0 |
| Sequential integer IDs | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 0 | 1.4094 | 0 | 1.4094 | 1.7031 | 0.4094 | 0.6552 | 3 | 11 | 7 |
| Sequential integer IDs | Fill-only | 0.5 | 0.5039 | Linear probing | 0 | 1.4094 | 0 | 1.4094 | 2.4156 | 0.4094 | 0.9509 | 5 | 11 | 0 |
| Sequential integer IDs | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 0 | 2.0292 | 0 | 2.0292 | 2.3236 | 1.0292 | 1.2725 | 6 | 24 | 38.8 |
| Sequential integer IDs | Fill-only | 0.7 | 0.7008 | Linear probing | 0 | 2.0292 | 0 | 2.0292 | 4.8517 | 1.0292 | 2.3582 | 18 | 24 | 0 |
| Sequential integer IDs | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 0 | 2.9667 | 0 | 2.9667 | 3.5185 | 1.9667 | 1.9395 | 10 | 80 | 96.8 |
| Sequential integer IDs | Fill-only | 0.85 | 0.8504 | Linear probing | 0 | 2.9667 | 0 | 2.9667 | 13.2204 | 1.9667 | 5.0573 | 58 | 80 | 0 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 10 | 1.2563 | 1.2 | 1.1545 | 1.2636 | 0.1545 | 0.4087 | 2 | 5 | 1.6 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 10 | 1.2563 | 1.16 | 1.1545 | 1.2636 | 0.1545 | 0.5255 | 4 | 5 | 0 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 19 | 1.4094 | 1.2947 | 1.2711 | 1.4133 | 0.2711 | 0.5435 | 2 | 8 | 7 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 19 | 1.4094 | 1.2947 | 1.2711 | 1.8178 | 0.2711 | 0.7132 | 5 | 8 | 0 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 27 | 2.0292 | 1.7333 | 1.4387 | 1.5774 | 0.4387 | 0.7281 | 4 | 17 | 38.8 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 27 | 2.0292 | 1.7333 | 1.4387 | 2.3484 | 0.4387 | 1.2499 | 14 | 17 | 0 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 32 | 2.9667 | 2.15 | 1.6842 | 2.0079 | 0.6842 | 0.9708 | 5 | 23 | 96.8 |
| Sequential integer IDs | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 32 | 2.9667 | 2.3438 | 1.6842 | 3.2737 | 0.6842 | 1.5493 | 14 | 23 | 0 |

## Probe-distance histograms

Counts are aggregated across deterministic trials so the variance story is visible without digging through the raw CSV/JSON exports; for delete-heavy runs, the histograms are captured after the deterministic removal pass.

### Random string IDs

#### Fill-only

##### Requested load factor 0.25 → remaining 0.252

32 starting entries per trial; 32 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 133 (83.1%) ██████████ | 137 (85.6%) ██████████ |
| 1 | 20 (12.5%) ██ | 14 (8.8%) █ |
| 2 | 7 (4.4%) █ | 8 (5.0%) █ |
| 4 | 0 (0.0%) | 1 (0.6%) █ |

##### Requested load factor 0.5 → remaining 0.5039

64 starting entries per trial; 64 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 228 (71.2%) █████████ | 247 (77.2%) █████████ |
| 1 | 67 (20.9%) ███ | 48 (15.0%) ██ |
| 2 | 21 (6.6%) █ | 15 (4.7%) █ |
| 3 | 4 (1.2%) █ | 5 (1.6%) █ |
| 4 | 0 (0.0%) | 1 (0.3%) █ |
| 5 | 0 (0.0%) | 1 (0.3%) █ |
| 6 | 0 (0.0%) | 2 (0.6%) █ |
| 7 | 0 (0.0%) | 1 (0.3%) █ |

##### Requested load factor 0.7 → remaining 0.7008

89 starting entries per trial; 89 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 195 (43.8%) █████ | 298 (67.0%) ████████ |
| 1 | 142 (31.9%) ████ | 64 (14.4%) ██ |
| 2 | 72 (16.2%) ██ | 28 (6.3%) █ |
| 3 | 32 (7.2%) █ | 15 (3.4%) █ |
| 4 | 4 (0.9%) █ | 14 (3.1%) █ |
| 5 | 0 (0.0%) | 8 (1.8%) █ |
| 6 | 0 (0.0%) | 8 (1.8%) █ |
| 7 | 0 (0.0%) | 2 (0.4%) █ |
| 8 | 0 (0.0%) | 4 (0.9%) █ |
| 9 | 0 (0.0%) | 2 (0.4%) █ |
| 10 | 0 (0.0%) | 1 (0.2%) █ |
| 15 | 0 (0.0%) | 1 (0.2%) █ |

##### Requested load factor 0.85 → remaining 0.8504

108 starting entries per trial; 108 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 123 (22.8%) ███ | 308 (57.0%) ███████ |
| 1 | 117 (21.7%) ███ | 86 (15.9%) ██ |
| 2 | 102 (18.9%) ██ | 44 (8.2%) █ |
| 3 | 75 (13.9%) ██ | 21 (3.9%) █ |
| 4 | 60 (11.1%) █ | 16 (3.0%) █ |
| 5 | 27 (5.0%) █ | 12 (2.2%) █ |
| 6 | 17 (3.1%) █ | 3 (0.6%) █ |
| 7 | 9 (1.7%) █ | 6 (1.1%) █ |
| 8 | 9 (1.7%) █ | 7 (1.3%) █ |
| 9 | 1 (0.2%) █ | 1 (0.2%) █ |
| 10 | 0 (0.0%) | 3 (0.6%) █ |
| 11 | 0 (0.0%) | 2 (0.4%) █ |
| 12 | 0 (0.0%) | 4 (0.7%) █ |
| 13 | 0 (0.0%) | 2 (0.4%) █ |
| 14 | 0 (0.0%) | 3 (0.6%) █ |
| 15 | 0 (0.0%) | 2 (0.4%) █ |
| 16 | 0 (0.0%) | 2 (0.4%) █ |
| 17 | 0 (0.0%) | 2 (0.4%) █ |
| 18 | 0 (0.0%) | 1 (0.2%) █ |
| 19 | 0 (0.0%) | 3 (0.6%) █ |
| 20 | 0 (0.0%) | 1 (0.2%) █ |
| 21 | 0 (0.0%) | 1 (0.2%) █ |
| 22 | 0 (0.0%) | 1 (0.2%) █ |
| 23 | 0 (0.0%) | 3 (0.6%) █ |
| 24 | 0 (0.0%) | 1 (0.2%) █ |
| 26 | 0 (0.0%) | 1 (0.2%) █ |
| 28 | 0 (0.0%) | 1 (0.2%) █ |
| 36 | 0 (0.0%) | 1 (0.2%) █ |
| 38 | 0 (0.0%) | 1 (0.2%) █ |
| 58 | 0 (0.0%) | 1 (0.2%) █ |

#### Delete-heavy (30.0% removals)

##### Requested load factor 0.25 → remaining 0.1732

32 starting entries per trial; 22 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 101 (91.8%) ███████████ | 102 (92.7%) ███████████ |
| 1 | 8 (7.3%) █ | 6 (5.5%) █ |
| 2 | 1 (0.9%) █ | 2 (1.8%) █ |

##### Requested load factor 0.5 → remaining 0.3543

64 starting entries per trial; 45 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 180 (80.0%) ██████████ | 186 (82.7%) ██████████ |
| 1 | 37 (16.4%) ██ | 28 (12.4%) █ |
| 2 | 8 (3.6%) █ | 8 (3.6%) █ |
| 3 | 0 (0.0%) | 3 (1.3%) █ |

##### Requested load factor 0.7 → remaining 0.4882

89 starting entries per trial; 62 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 203 (65.5%) ████████ | 233 (75.2%) █████████ |
| 1 | 81 (26.1%) ███ | 43 (13.9%) ██ |
| 2 | 24 (7.7%) █ | 20 (6.5%) █ |
| 3 | 2 (0.7%) █ | 7 (2.3%) █ |
| 4 | 0 (0.0%) | 4 (1.3%) █ |
| 5 | 0 (0.0%) | 3 (1.0%) █ |

##### Requested load factor 0.85 → remaining 0.5984

108 starting entries per trial; 76 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 214 (56.3%) ███████ | 265 (69.7%) ████████ |
| 1 | 100 (26.3%) ███ | 50 (13.2%) ██ |
| 2 | 43 (11.3%) █ | 34 (8.9%) █ |
| 3 | 16 (4.2%) █ | 16 (4.2%) █ |
| 4 | 6 (1.6%) █ | 6 (1.6%) █ |
| 5 | 1 (0.3%) █ | 1 (0.3%) █ |
| 6 | 0 (0.0%) | 2 (0.5%) █ |
| 7 | 0 (0.0%) | 1 (0.3%) █ |
| 8 | 0 (0.0%) | 1 (0.3%) █ |
| 9 | 0 (0.0%) | 1 (0.3%) █ |
| 10 | 0 (0.0%) | 1 (0.3%) █ |
| 11 | 0 (0.0%) | 2 (0.5%) █ |

### Sequential integer IDs

#### Fill-only

##### Requested load factor 0.25 → remaining 0.252

32 starting entries per trial; 32 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 130 (81.2%) ██████████ | 134 (83.8%) ██████████ |
| 1 | 24 (15.0%) ██ | 19 (11.9%) █ |
| 2 | 3 (1.9%) █ | 4 (2.5%) █ |
| 3 | 1 (0.6%) █ | 1 (0.6%) █ |
| 4 | 2 (1.2%) █ | 0 (0.0%) |
| 5 | 0 (0.0%) | 1 (0.6%) █ |
| 6 | 0 (0.0%) | 1 (0.6%) █ |

##### Requested load factor 0.5 → remaining 0.5039

64 starting entries per trial; 64 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 216 (67.5%) ████████ | 248 (77.5%) █████████ |
| 1 | 80 (25.0%) ███ | 43 (13.4%) ██ |
| 2 | 21 (6.6%) █ | 12 (3.8%) █ |
| 3 | 3 (0.9%) █ | 8 (2.5%) █ |
| 4 | 0 (0.0%) | 5 (1.6%) █ |
| 5 | 0 (0.0%) | 4 (1.2%) █ |

##### Requested load factor 0.7 → remaining 0.7008

89 starting entries per trial; 89 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 194 (43.6%) █████ | 293 (65.8%) ████████ |
| 1 | 141 (31.7%) ████ | 65 (14.6%) ██ |
| 2 | 60 (13.5%) ██ | 30 (6.7%) █ |
| 3 | 18 (4.0%) █ | 23 (5.2%) █ |
| 4 | 18 (4.0%) █ | 6 (1.4%) █ |
| 5 | 13 (2.9%) █ | 7 (1.6%) █ |
| 6 | 1 (0.2%) █ | 4 (0.9%) █ |
| 7 | 0 (0.0%) | 5 (1.1%) █ |
| 8 | 0 (0.0%) | 2 (0.4%) █ |
| 9 | 0 (0.0%) | 1 (0.2%) █ |
| 10 | 0 (0.0%) | 2 (0.4%) █ |
| 12 | 0 (0.0%) | 2 (0.4%) █ |
| 14 | 0 (0.0%) | 2 (0.4%) █ |
| 15 | 0 (0.0%) | 1 (0.2%) █ |
| 16 | 0 (0.0%) | 1 (0.2%) █ |
| 18 | 0 (0.0%) | 1 (0.2%) █ |

##### Requested load factor 0.85 → remaining 0.8504

108 starting entries per trial; 108 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 134 (24.8%) ███ | 311 (57.6%) ███████ |
| 1 | 136 (25.2%) ███ | 88 (16.3%) ██ |
| 2 | 99 (18.3%) ██ | 37 (6.9%) █ |
| 3 | 85 (15.7%) ██ | 26 (4.8%) █ |
| 4 | 34 (6.3%) █ | 17 (3.1%) █ |
| 5 | 16 (3.0%) █ | 11 (2.0%) █ |
| 6 | 13 (2.4%) █ | 6 (1.1%) █ |
| 7 | 11 (2.0%) █ | 6 (1.1%) █ |
| 8 | 7 (1.3%) █ | 6 (1.1%) █ |
| 9 | 4 (0.7%) █ | 3 (0.6%) █ |
| 10 | 1 (0.2%) █ | 3 (0.6%) █ |
| 11 | 0 (0.0%) | 2 (0.4%) █ |
| 12 | 0 (0.0%) | 3 (0.6%) █ |
| 13 | 0 (0.0%) | 3 (0.6%) █ |
| 14 | 0 (0.0%) | 3 (0.6%) █ |
| 15 | 0 (0.0%) | 2 (0.4%) █ |
| 16 | 0 (0.0%) | 1 (0.2%) █ |
| 17 | 0 (0.0%) | 2 (0.4%) █ |
| 18 | 0 (0.0%) | 1 (0.2%) █ |
| 19 | 0 (0.0%) | 1 (0.2%) █ |
| 21 | 0 (0.0%) | 1 (0.2%) █ |
| 23 | 0 (0.0%) | 1 (0.2%) █ |
| 26 | 0 (0.0%) | 1 (0.2%) █ |
| 27 | 0 (0.0%) | 1 (0.2%) █ |
| 28 | 0 (0.0%) | 2 (0.4%) █ |
| 49 | 0 (0.0%) | 1 (0.2%) █ |
| 58 | 0 (0.0%) | 1 (0.2%) █ |

#### Delete-heavy (30.0% removals)

##### Requested load factor 0.25 → remaining 0.1732

32 starting entries per trial; 22 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 95 (86.4%) ██████████ | 98 (89.1%) ███████████ |
| 1 | 13 (11.8%) █ | 9 (8.2%) █ |
| 2 | 2 (1.8%) █ | 2 (1.8%) █ |
| 4 | 0 (0.0%) | 1 (0.9%) █ |

##### Requested load factor 0.5 → remaining 0.3543

64 starting entries per trial; 45 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 175 (77.8%) █████████ | 186 (82.7%) ██████████ |
| 1 | 39 (17.3%) ██ | 26 (11.6%) █ |
| 2 | 11 (4.9%) █ | 7 (3.1%) █ |
| 3 | 0 (0.0%) | 4 (1.8%) █ |
| 4 | 0 (0.0%) | 1 (0.4%) █ |
| 5 | 0 (0.0%) | 1 (0.4%) █ |

##### Requested load factor 0.7 → remaining 0.4882

89 starting entries per trial; 62 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 206 (66.5%) ████████ | 240 (77.4%) █████████ |
| 1 | 83 (26.8%) ███ | 42 (13.6%) ██ |
| 2 | 11 (3.5%) █ | 15 (4.8%) █ |
| 3 | 9 (2.9%) █ | 7 (2.3%) █ |
| 4 | 1 (0.3%) █ | 1 (0.3%) █ |
| 5 | 0 (0.0%) | 2 (0.7%) █ |
| 6 | 0 (0.0%) | 1 (0.3%) █ |
| 9 | 0 (0.0%) | 1 (0.3%) █ |
| 14 | 0 (0.0%) | 1 (0.3%) █ |

##### Requested load factor 0.85 → remaining 0.5984

108 starting entries per trial; 76 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 215 (56.6%) ███████ | 265 (69.7%) ████████ |
| 1 | 103 (27.1%) ███ | 59 (15.5%) ██ |
| 2 | 38 (10.0%) █ | 24 (6.3%) █ |
| 3 | 16 (4.2%) █ | 13 (3.4%) █ |
| 4 | 7 (1.8%) █ | 9 (2.4%) █ |
| 5 | 1 (0.3%) █ | 2 (0.5%) █ |
| 6 | 0 (0.0%) | 2 (0.5%) █ |
| 7 | 0 (0.0%) | 1 (0.3%) █ |
| 8 | 0 (0.0%) | 1 (0.3%) █ |
| 9 | 0 (0.0%) | 3 (0.8%) █ |
| 14 | 0 (0.0%) | 1 (0.3%) █ |

## Unsuccessful-lookup histograms

Counts are aggregated across deterministic trials after each workload finishes, so failed-search cost is visible alongside the resident probe-distance story.

### Random string IDs

#### Fill-only

##### Requested load factor 0.25 → remaining 0.252

32 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 32 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 119 (74.4%) █████████ | 119 (74.4%) █████████ |
| 2 | 38 (23.8%) ███ | 28 (17.5%) ██ |
| 3 | 1 (0.6%) █ | 9 (5.6%) █ |
| 4 | 2 (1.2%) █ | 2 (1.2%) █ |
| 9 | 0 (0.0%) | 2 (1.2%) █ |

##### Requested load factor 0.5 → remaining 0.5039

64 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 64 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 144 (45.0%) █████ | 168 (52.5%) ██████ |
| 2 | 119 (37.2%) ████ | 75 (23.4%) ███ |
| 3 | 46 (14.4%) ██ | 24 (7.5%) █ |
| 4 | 9 (2.8%) █ | 18 (5.6%) █ |
| 5 | 2 (0.6%) █ | 9 (2.8%) █ |
| 6 | 0 (0.0%) | 13 (4.1%) █ |
| 7 | 0 (0.0%) | 4 (1.2%) █ |
| 8 | 0 (0.0%) | 4 (1.2%) █ |
| 9 | 0 (0.0%) | 4 (1.2%) █ |
| 10 | 0 (0.0%) | 1 (0.3%) █ |

##### Requested load factor 0.7 → remaining 0.7008

89 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 89 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 125 (28.1%) ███ | 110 (24.7%) ███ |
| 2 | 132 (29.7%) ████ | 68 (15.3%) ██ |
| 3 | 118 (26.5%) ███ | 37 (8.3%) █ |
| 4 | 47 (10.6%) █ | 41 (9.2%) █ |
| 5 | 21 (4.7%) █ | 27 (6.1%) █ |
| 6 | 2 (0.4%) █ | 25 (5.6%) █ |
| 7 | 0 (0.0%) | 20 (4.5%) █ |
| 8 | 0 (0.0%) | 16 (3.6%) █ |
| 9 | 0 (0.0%) | 21 (4.7%) █ |
| 10 | 0 (0.0%) | 13 (2.9%) █ |
| 11 | 0 (0.0%) | 10 (2.2%) █ |
| 12 | 0 (0.0%) | 14 (3.1%) █ |
| 13 | 0 (0.0%) | 5 (1.1%) █ |
| 14 | 0 (0.0%) | 10 (2.2%) █ |
| 15 | 0 (0.0%) | 9 (2.0%) █ |
| 16 | 0 (0.0%) | 4 (0.9%) █ |
| 17 | 0 (0.0%) | 5 (1.1%) █ |
| 18 | 0 (0.0%) | 4 (0.9%) █ |
| 20 | 0 (0.0%) | 4 (0.9%) █ |
| 22 | 0 (0.0%) | 2 (0.4%) █ |

##### Requested load factor 0.85 → remaining 0.8504

108 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 108 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 68 (12.6%) ██ | 90 (16.7%) ██ |
| 2 | 104 (19.3%) ██ | 38 (7.0%) █ |
| 3 | 106 (19.6%) ██ | 30 (5.6%) █ |
| 4 | 99 (18.3%) ██ | 28 (5.2%) █ |
| 5 | 74 (13.7%) ██ | 30 (5.6%) █ |
| 6 | 42 (7.8%) █ | 13 (2.4%) █ |
| 7 | 25 (4.6%) █ | 9 (1.7%) █ |
| 8 | 11 (2.0%) █ | 15 (2.8%) █ |
| 9 | 5 (0.9%) █ | 14 (2.6%) █ |
| 10 | 4 (0.7%) █ | 16 (3.0%) █ |
| 11 | 2 (0.4%) █ | 15 (2.8%) █ |
| 12 | 0 (0.0%) | 8 (1.5%) █ |
| 13 | 0 (0.0%) | 6 (1.1%) █ |
| 14 | 0 (0.0%) | 6 (1.1%) █ |
| 15 | 0 (0.0%) | 5 (0.9%) █ |
| 16 | 0 (0.0%) | 9 (1.7%) █ |
| 17 | 0 (0.0%) | 9 (1.7%) █ |
| 18 | 0 (0.0%) | 10 (1.8%) █ |
| 19 | 0 (0.0%) | 6 (1.1%) █ |
| 20 | 0 (0.0%) | 8 (1.5%) █ |
| 21 | 0 (0.0%) | 4 (0.7%) █ |
| 22 | 0 (0.0%) | 11 (2.0%) █ |
| 23 | 0 (0.0%) | 4 (0.7%) █ |
| 24 | 0 (0.0%) | 7 (1.3%) █ |
| 25 | 0 (0.0%) | 8 (1.5%) █ |
| 26 | 0 (0.0%) | 1 (0.2%) █ |
| 27 | 0 (0.0%) | 6 (1.1%) █ |
| 28 | 0 (0.0%) | 6 (1.1%) █ |
| 29 | 0 (0.0%) | 5 (0.9%) █ |
| 30 | 0 (0.0%) | 2 (0.4%) █ |
| 31 | 0 (0.0%) | 5 (0.9%) █ |
| 32 | 0 (0.0%) | 4 (0.7%) █ |
| 33 | 0 (0.0%) | 3 (0.6%) █ |
| 34 | 0 (0.0%) | 8 (1.5%) █ |
| 35 | 0 (0.0%) | 7 (1.3%) █ |
| 36 | 0 (0.0%) | 6 (1.1%) █ |
| 37 | 0 (0.0%) | 2 (0.4%) █ |
| 38 | 0 (0.0%) | 5 (0.9%) █ |
| 39 | 0 (0.0%) | 3 (0.6%) █ |
| 40 | 0 (0.0%) | 5 (0.9%) █ |
| 41 | 0 (0.0%) | 2 (0.4%) █ |
| 42 | 0 (0.0%) | 8 (1.5%) █ |
| 43 | 0 (0.0%) | 4 (0.7%) █ |
| 44 | 0 (0.0%) | 6 (1.1%) █ |
| 45 | 0 (0.0%) | 2 (0.4%) █ |
| 46 | 0 (0.0%) | 3 (0.6%) █ |
| 47 | 0 (0.0%) | 8 (1.5%) █ |
| 48 | 0 (0.0%) | 4 (0.7%) █ |
| 49 | 0 (0.0%) | 2 (0.4%) █ |
| 50 | 0 (0.0%) | 2 (0.4%) █ |
| 51 | 0 (0.0%) | 2 (0.4%) █ |
| 52 | 0 (0.0%) | 1 (0.2%) █ |
| 54 | 0 (0.0%) | 5 (0.9%) █ |
| 56 | 0 (0.0%) | 2 (0.4%) █ |
| 57 | 0 (0.0%) | 1 (0.2%) █ |
| 58 | 0 (0.0%) | 2 (0.4%) █ |
| 59 | 0 (0.0%) | 2 (0.4%) █ |
| 60 | 0 (0.0%) | 1 (0.2%) █ |
| 61 | 0 (0.0%) | 1 (0.2%) █ |
| 62 | 0 (0.0%) | 1 (0.2%) █ |
| 64 | 0 (0.0%) | 1 (0.2%) █ |
| 65 | 0 (0.0%) | 1 (0.2%) █ |
| 69 | 0 (0.0%) | 2 (0.4%) █ |
| 72 | 0 (0.0%) | 3 (0.6%) █ |
| 73 | 0 (0.0%) | 3 (0.6%) █ |
| 75 | 0 (0.0%) | 2 (0.4%) █ |
| 76 | 0 (0.0%) | 1 (0.2%) █ |
| 79 | 0 (0.0%) | 1 (0.2%) █ |

#### Delete-heavy (30.0% removals)

##### Requested load factor 0.25 → remaining 0.1732

22 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 22 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 89 (80.9%) ██████████ | 89 (80.9%) ██████████ |
| 2 | 20 (18.2%) ██ | 14 (12.7%) ██ |
| 3 | 0 (0.0%) | 6 (5.5%) █ |
| 4 | 1 (0.9%) █ | 0 (0.0%) |
| 5 | 0 (0.0%) | 1 (0.9%) █ |

##### Requested load factor 0.5 → remaining 0.3543

45 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 45 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 139 (61.8%) ███████ | 153 (68.0%) ████████ |
| 2 | 63 (28.0%) ███ | 40 (17.8%) ██ |
| 3 | 22 (9.8%) █ | 18 (8.0%) █ |
| 4 | 1 (0.4%) █ | 9 (4.0%) █ |
| 5 | 0 (0.0%) | 1 (0.4%) █ |
| 6 | 0 (0.0%) | 4 (1.8%) █ |

##### Requested load factor 0.7 → remaining 0.4882

62 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 62 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 161 (51.9%) ██████ | 166 (53.5%) ██████ |
| 2 | 106 (34.2%) ████ | 61 (19.7%) ██ |
| 3 | 35 (11.3%) █ | 33 (10.7%) █ |
| 4 | 8 (2.6%) █ | 22 (7.1%) █ |
| 5 | 0 (0.0%) | 10 (3.2%) █ |
| 6 | 0 (0.0%) | 6 (1.9%) █ |
| 7 | 0 (0.0%) | 6 (1.9%) █ |
| 8 | 0 (0.0%) | 3 (1.0%) █ |
| 9 | 0 (0.0%) | 1 (0.3%) █ |
| 10 | 0 (0.0%) | 1 (0.3%) █ |
| 11 | 0 (0.0%) | 1 (0.3%) █ |

##### Requested load factor 0.85 → remaining 0.5984

76 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 76 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 164 (43.2%) █████ | 145 (38.2%) █████ |
| 2 | 118 (31.1%) ████ | 69 (18.2%) ██ |
| 3 | 58 (15.3%) ██ | 42 (11.1%) █ |
| 4 | 26 (6.8%) █ | 29 (7.6%) █ |
| 5 | 9 (2.4%) █ | 24 (6.3%) █ |
| 6 | 5 (1.3%) █ | 15 (4.0%) █ |
| 7 | 0 (0.0%) | 17 (4.5%) █ |
| 8 | 0 (0.0%) | 7 (1.8%) █ |
| 9 | 0 (0.0%) | 4 (1.1%) █ |
| 10 | 0 (0.0%) | 5 (1.3%) █ |
| 11 | 0 (0.0%) | 5 (1.3%) █ |
| 12 | 0 (0.0%) | 2 (0.5%) █ |
| 13 | 0 (0.0%) | 4 (1.1%) █ |
| 14 | 0 (0.0%) | 3 (0.8%) █ |
| 15 | 0 (0.0%) | 2 (0.5%) █ |
| 16 | 0 (0.0%) | 2 (0.5%) █ |
| 17 | 0 (0.0%) | 4 (1.1%) █ |
| 20 | 0 (0.0%) | 1 (0.3%) █ |

### Sequential integer IDs

#### Fill-only

##### Requested load factor 0.25 → remaining 0.252

32 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 32 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 127 (79.4%) ██████████ | 125 (78.1%) █████████ |
| 2 | 30 (18.8%) ██ | 24 (15.0%) ██ |
| 3 | 2 (1.2%) █ | 7 (4.4%) █ |
| 4 | 0 (0.0%) | 4 (2.5%) █ |
| 6 | 1 (0.6%) █ | 0 (0.0%) |

##### Requested load factor 0.5 → remaining 0.5039

64 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 64 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 169 (52.8%) ██████ | 159 (49.7%) ██████ |
| 2 | 92 (28.7%) ███ | 68 (21.2%) ███ |
| 3 | 44 (13.8%) ██ | 30 (9.4%) █ |
| 4 | 15 (4.7%) █ | 20 (6.2%) █ |
| 5 | 0 (0.0%) | 9 (2.8%) █ |
| 6 | 0 (0.0%) | 9 (2.8%) █ |
| 7 | 0 (0.0%) | 7 (2.2%) █ |
| 8 | 0 (0.0%) | 9 (2.8%) █ |
| 9 | 0 (0.0%) | 4 (1.2%) █ |
| 10 | 0 (0.0%) | 3 (0.9%) █ |
| 11 | 0 (0.0%) | 2 (0.6%) █ |

##### Requested load factor 0.7 → remaining 0.7008

89 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 89 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 143 (32.1%) ████ | 128 (28.8%) ███ |
| 2 | 136 (30.6%) ████ | 67 (15.1%) ██ |
| 3 | 104 (23.4%) ███ | 45 (10.1%) █ |
| 4 | 30 (6.7%) █ | 42 (9.4%) █ |
| 5 | 12 (2.7%) █ | 27 (6.1%) █ |
| 6 | 14 (3.1%) █ | 28 (6.3%) █ |
| 7 | 5 (1.1%) █ | 14 (3.1%) █ |
| 8 | 1 (0.2%) █ | 11 (2.5%) █ |
| 9 | 0 (0.0%) | 15 (3.4%) █ |
| 10 | 0 (0.0%) | 12 (2.7%) █ |
| 11 | 0 (0.0%) | 9 (2.0%) █ |
| 12 | 0 (0.0%) | 9 (2.0%) █ |
| 13 | 0 (0.0%) | 5 (1.1%) █ |
| 14 | 0 (0.0%) | 3 (0.7%) █ |
| 15 | 0 (0.0%) | 5 (1.1%) █ |
| 16 | 0 (0.0%) | 4 (0.9%) █ |
| 17 | 0 (0.0%) | 5 (1.1%) █ |
| 18 | 0 (0.0%) | 5 (1.1%) █ |
| 19 | 0 (0.0%) | 5 (1.1%) █ |
| 20 | 0 (0.0%) | 3 (0.7%) █ |
| 21 | 0 (0.0%) | 1 (0.2%) █ |
| 22 | 0 (0.0%) | 1 (0.2%) █ |
| 24 | 0 (0.0%) | 1 (0.2%) █ |

##### Requested load factor 0.85 → remaining 0.8504

108 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 108 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 85 (15.7%) ██ | 83 (15.4%) ██ |
| 2 | 115 (21.3%) ███ | 59 (10.9%) █ |
| 3 | 112 (20.7%) ██ | 41 (7.6%) █ |
| 4 | 85 (15.7%) ██ | 38 (7.0%) █ |
| 5 | 65 (12.0%) █ | 31 (5.7%) █ |
| 6 | 30 (5.6%) █ | 26 (4.8%) █ |
| 7 | 15 (2.8%) █ | 26 (4.8%) █ |
| 8 | 14 (2.6%) █ | 18 (3.3%) █ |
| 9 | 7 (1.3%) █ | 10 (1.8%) █ |
| 10 | 9 (1.7%) █ | 13 (2.4%) █ |
| 11 | 2 (0.4%) █ | 12 (2.2%) █ |
| 12 | 1 (0.2%) █ | 11 (2.0%) █ |
| 13 | 0 (0.0%) | 7 (1.3%) █ |
| 14 | 0 (0.0%) | 7 (1.3%) █ |
| 15 | 0 (0.0%) | 5 (0.9%) █ |
| 16 | 0 (0.0%) | 9 (1.7%) █ |
| 17 | 0 (0.0%) | 6 (1.1%) █ |
| 18 | 0 (0.0%) | 3 (0.6%) █ |
| 19 | 0 (0.0%) | 7 (1.3%) █ |
| 20 | 0 (0.0%) | 5 (0.9%) █ |
| 21 | 0 (0.0%) | 4 (0.7%) █ |
| 22 | 0 (0.0%) | 8 (1.5%) █ |
| 23 | 0 (0.0%) | 6 (1.1%) █ |
| 24 | 0 (0.0%) | 9 (1.7%) █ |
| 25 | 0 (0.0%) | 7 (1.3%) █ |
| 26 | 0 (0.0%) | 4 (0.7%) █ |
| 27 | 0 (0.0%) | 6 (1.1%) █ |
| 28 | 0 (0.0%) | 7 (1.3%) █ |
| 29 | 0 (0.0%) | 1 (0.2%) █ |
| 30 | 0 (0.0%) | 5 (0.9%) █ |
| 31 | 0 (0.0%) | 6 (1.1%) █ |
| 32 | 0 (0.0%) | 3 (0.6%) █ |
| 33 | 0 (0.0%) | 2 (0.4%) █ |
| 34 | 0 (0.0%) | 2 (0.4%) █ |
| 36 | 0 (0.0%) | 6 (1.1%) █ |
| 37 | 0 (0.0%) | 2 (0.4%) █ |
| 38 | 0 (0.0%) | 1 (0.2%) █ |
| 39 | 0 (0.0%) | 2 (0.4%) █ |
| 40 | 0 (0.0%) | 2 (0.4%) █ |
| 41 | 0 (0.0%) | 2 (0.4%) █ |
| 42 | 0 (0.0%) | 1 (0.2%) █ |
| 43 | 0 (0.0%) | 2 (0.4%) █ |
| 44 | 0 (0.0%) | 1 (0.2%) █ |
| 45 | 0 (0.0%) | 1 (0.2%) █ |
| 46 | 0 (0.0%) | 2 (0.4%) █ |
| 48 | 0 (0.0%) | 1 (0.2%) █ |
| 49 | 0 (0.0%) | 2 (0.4%) █ |
| 54 | 0 (0.0%) | 2 (0.4%) █ |
| 55 | 0 (0.0%) | 1 (0.2%) █ |
| 56 | 0 (0.0%) | 1 (0.2%) █ |
| 57 | 0 (0.0%) | 3 (0.6%) █ |
| 58 | 0 (0.0%) | 1 (0.2%) █ |
| 60 | 0 (0.0%) | 1 (0.2%) █ |
| 62 | 0 (0.0%) | 2 (0.4%) █ |
| 65 | 0 (0.0%) | 1 (0.2%) █ |
| 68 | 0 (0.0%) | 2 (0.4%) █ |
| 70 | 0 (0.0%) | 1 (0.2%) █ |
| 72 | 0 (0.0%) | 3 (0.6%) █ |
| 73 | 0 (0.0%) | 2 (0.4%) █ |
| 75 | 0 (0.0%) | 2 (0.4%) █ |
| 76 | 0 (0.0%) | 2 (0.4%) █ |
| 77 | 0 (0.0%) | 3 (0.6%) █ |
| 78 | 0 (0.0%) | 1 (0.2%) █ |

#### Delete-heavy (30.0% removals)

##### Requested load factor 0.25 → remaining 0.1732

22 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 22 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 85 (77.3%) █████████ | 91 (82.7%) ██████████ |
| 2 | 22 (20.0%) ██ | 11 (10.0%) █ |
| 3 | 2 (1.8%) █ | 6 (5.5%) █ |
| 4 | 1 (0.9%) █ | 2 (1.8%) █ |

##### Requested load factor 0.5 → remaining 0.3543

45 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 45 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 156 (69.3%) ████████ | 139 (61.8%) ███████ |
| 2 | 49 (21.8%) ███ | 45 (20.0%) ██ |
| 3 | 16 (7.1%) █ | 16 (7.1%) █ |
| 4 | 4 (1.8%) █ | 10 (4.4%) █ |
| 5 | 0 (0.0%) | 5 (2.2%) █ |
| 6 | 0 (0.0%) | 5 (2.2%) █ |
| 7 | 0 (0.0%) | 3 (1.3%) █ |
| 8 | 0 (0.0%) | 2 (0.9%) █ |

##### Requested load factor 0.7 → remaining 0.4882

62 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 62 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 176 (56.8%) ███████ | 151 (48.7%) ██████ |
| 2 | 100 (32.3%) ████ | 68 (21.9%) ███ |
| 3 | 28 (9.0%) █ | 35 (11.3%) █ |
| 4 | 2 (0.7%) █ | 24 (7.7%) █ |
| 5 | 3 (1.0%) █ | 9 (2.9%) █ |
| 6 | 1 (0.3%) █ | 4 (1.3%) █ |
| 7 | 0 (0.0%) | 10 (3.2%) █ |
| 8 | 0 (0.0%) | 2 (0.7%) █ |
| 9 | 0 (0.0%) | 2 (0.7%) █ |
| 11 | 0 (0.0%) | 3 (1.0%) █ |
| 16 | 0 (0.0%) | 1 (0.3%) █ |
| 18 | 0 (0.0%) | 1 (0.3%) █ |

##### Requested load factor 0.85 → remaining 0.5984

76 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 76 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 147 (38.7%) █████ | 143 (37.6%) █████ |
| 2 | 136 (35.8%) ████ | 79 (20.8%) ██ |
| 3 | 61 (16.1%) ██ | 43 (11.3%) █ |
| 4 | 23 (6.0%) █ | 30 (7.9%) █ |
| 5 | 10 (2.6%) █ | 25 (6.6%) █ |
| 6 | 2 (0.5%) █ | 15 (4.0%) █ |
| 7 | 1 (0.3%) █ | 6 (1.6%) █ |
| 8 | 0 (0.0%) | 5 (1.3%) █ |
| 9 | 0 (0.0%) | 8 (2.1%) █ |
| 10 | 0 (0.0%) | 7 (1.8%) █ |
| 11 | 0 (0.0%) | 6 (1.6%) █ |
| 12 | 0 (0.0%) | 5 (1.3%) █ |
| 13 | 0 (0.0%) | 1 (0.3%) █ |
| 15 | 0 (0.0%) | 3 (0.8%) █ |
| 16 | 0 (0.0%) | 1 (0.3%) █ |
| 17 | 0 (0.0%) | 1 (0.3%) █ |
| 18 | 0 (0.0%) | 1 (0.3%) █ |
| 20 | 0 (0.0%) | 1 (0.3%) █ |


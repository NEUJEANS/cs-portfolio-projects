# Robin Hood hashing benchmark comparison with delete-heavy workloads

Deterministic benchmark report comparing Robin Hood hashing against a linear-probing baseline, with resident probe-distance histograms plus hit/miss lookup percentile callouts that make both dispersion and tail cost visible at a glance. It also includes a delete-heavy workload that removes 30.0% of keys before the final hit/miss lookup + histogram pass, so post-removal clustering is visible too. It also compares Random string IDs and Sequential integer IDs, so the same workloads can be narrated as longer text-like IDs versus compact numeric IDs while keeping the snapshot format string-only. It also compares Uniform spread and Collision-focused hotspots, so the same identifier shapes can be replayed under both naturally spread keys and intentionally clustered hotspot keys.

- Capacity: 127
- Trials per workload/load factor: 5
- Key profiles: Random string IDs, Sequential integer IDs
- Key presets: Uniform spread, Collision-focused hotspots
- Strategies: Robin Hood hashing, Linear probing
- Workloads: Fill-only, Delete-heavy (30.0% removals)
- Requested load factors: 0.25, 0.5, 0.7, 0.85
- Note: requested load factors are rounded to whole entry counts, so the effective fill level can differ slightly from the requested target.

## Headline comparisons

| Key profile / preset | Workload | Requested load factor | Remaining load factor | Remaining entries | Successful lookup winner | Success delta vs linear | Unsuccessful lookup winner | Miss delta vs linear | Lower probe-distance stddev | Stddev delta vs linear | Lower delete probes | Delete delta vs linear |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- | ---: | --- | ---: |
| Random string IDs · Uniform spread | Fill-only | 0.25 | 0.252 | 32 | Tie | 0 | Robin Hood hashing | 0.1375 | Robin Hood hashing | 0.0803 | — | — |
| Random string IDs · Uniform spread | Fill-only | 0.5 | 0.5039 | 64 | Tie | 0 | Robin Hood hashing | 0.3906 | Robin Hood hashing | 0.2529 | — | — |
| Random string IDs · Uniform spread | Fill-only | 0.7 | 0.7008 | 89 | Tie | 0 | Robin Hood hashing | 2.9393 | Robin Hood hashing | 0.8624 | — | — |
| Random string IDs · Uniform spread | Fill-only | 0.85 | 0.8504 | 108 | Tie | 0 | Robin Hood hashing | 13.4074 | Robin Hood hashing | 3.415 | — | — |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | 22 | Tie | 0 | Robin Hood hashing | 0.0091 | Robin Hood hashing | 0.0275 | Linear probing | -0.04 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | 45 | Tie | 0 | Robin Hood hashing | 0.0266 | Robin Hood hashing | 0.0933 | Robin Hood hashing | 0.0737 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | 62 | Tie | 0 | Robin Hood hashing | 0.7097 | Robin Hood hashing | 0.2606 | Robin Hood hashing | 0.1482 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | 76 | Tie | 0 | Robin Hood hashing | 1.1158 | Robin Hood hashing | 0.6614 | Robin Hood hashing | 0.1375 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.25 | 0.252 | 32 | Tie | 0 | Linear probing | -0.2438 | Robin Hood hashing | 1.2476 | — | — |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.5 | 0.5039 | 64 | Tie | 0 | Robin Hood hashing | 3.7812 | Robin Hood hashing | 3.3593 | — | — |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.7 | 0.7008 | 89 | Tie | 0 | Robin Hood hashing | 6.5888 | Robin Hood hashing | 8.3668 | — | — |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.85 | 0.8504 | 108 | Tie | 0 | Robin Hood hashing | 15.7389 | Robin Hood hashing | 6.6673 | — | — |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | 22 | Tie | 0 | Linear probing | -0.4091 | Robin Hood hashing | 1.0294 | Linear probing | -0.46 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | 45 | Tie | 0 | Robin Hood hashing | 4.1911 | Robin Hood hashing | 1.7243 | Linear probing | -0.3895 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | 62 | Tie | 0 | Robin Hood hashing | 1.9483 | Robin Hood hashing | 3.1184 | Robin Hood hashing | 0.2741 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | 76 | Tie | 0 | Robin Hood hashing | 3.9895 | Robin Hood hashing | 2.3815 | Linear probing | -1.8937 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.25 | 0.252 | 32 | Tie | 0 | Robin Hood hashing | 0.0688 | Robin Hood hashing | 0.1238 | — | — |
| Sequential integer IDs · Uniform spread | Fill-only | 0.5 | 0.5039 | 64 | Tie | 0 | Robin Hood hashing | 0.7125 | Robin Hood hashing | 0.2957 | — | — |
| Sequential integer IDs · Uniform spread | Fill-only | 0.7 | 0.7008 | 89 | Tie | 0 | Robin Hood hashing | 2.5281 | Robin Hood hashing | 1.0857 | — | — |
| Sequential integer IDs · Uniform spread | Fill-only | 0.85 | 0.8504 | 108 | Tie | 0 | Robin Hood hashing | 9.7019 | Robin Hood hashing | 3.1178 | — | — |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | 22 | Tie | 0 | Linear probing | -0.0364 | Robin Hood hashing | 0.1517 | Robin Hood hashing | 0.02 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | 45 | Tie | 0 | Robin Hood hashing | 0.3111 | Robin Hood hashing | 0.1652 | Robin Hood hashing | 0.021 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | 62 | Tie | 0 | Robin Hood hashing | 0.6194 | Robin Hood hashing | 0.2504 | Tie | 0 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | 76 | Tie | 0 | Robin Hood hashing | 1.5736 | Robin Hood hashing | 0.4662 | Robin Hood hashing | 0.1437 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.25 | 0.252 | 32 | Tie | 0 | Linear probing | -0.7125 | Robin Hood hashing | 0.1485 | — | — |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.5 | 0.5039 | 64 | Tie | 0 | Robin Hood hashing | 3.05 | Robin Hood hashing | 2.3397 | — | — |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.7 | 0.7008 | 89 | Tie | 0 | Robin Hood hashing | 5.9618 | Robin Hood hashing | 3.4552 | — | — |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.85 | 0.8504 | 108 | Tie | 0 | Robin Hood hashing | 9.3389 | Robin Hood hashing | 8.4213 | — | — |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | 22 | Tie | 0 | Robin Hood hashing | 0.2727 | Tie | 0 | Robin Hood hashing | 0.04 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | 45 | Tie | 0 | Robin Hood hashing | 0.7912 | Robin Hood hashing | 0.384 | Robin Hood hashing | 0.4631 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | 62 | Tie | 0 | Robin Hood hashing | 1.0548 | Robin Hood hashing | 1.1636 | Robin Hood hashing | 0.9778 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | 76 | Tie | 0 | Robin Hood hashing | 7.6342 | Robin Hood hashing | 3.0349 | Linear probing | -1.2001 |

## Lookup percentile callouts

These side-by-side lookup summaries make hit and miss tails readable without scanning the full histograms.

| Key profile / preset | Workload | Requested load factor | Remaining load factor | Strategy | Successful lookups avg / p50 / p95 / max | Unsuccessful lookups avg / p50 / p95 / max |
| --- | --- | ---: | ---: | --- | --- | --- |
| Random string IDs · Uniform spread | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 1.2125 / 1 / 2 / 3 | 1.2875 / 1 / 2 / 4 |
| Random string IDs · Uniform spread | Fill-only | 0.25 | 0.252 | Linear probing | 1.2125 / 1 / 3 / 5 | 1.425 / 1 / 3 / 9 |
| Random string IDs · Uniform spread | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 1.3781 / 1 / 3 / 4 | 1.7688 / 2 / 3 / 5 |
| Random string IDs · Uniform spread | Fill-only | 0.5 | 0.5039 | Linear probing | 1.3781 / 1 / 3 / 8 | 2.1594 / 1 / 6 / 10 |
| Random string IDs · Uniform spread | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 1.8944 / 2 / 4 / 5 | 2.3551 / 2 / 5 / 6 |
| Random string IDs · Uniform spread | Fill-only | 0.7 | 0.7008 | Linear probing | 1.8944 / 1 / 6 / 16 | 5.2944 / 4 / 15 / 22 |
| Random string IDs · Uniform spread | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 3.1611 / 3 / 7 / 10 | 3.6704 / 3 / 7 / 11 |
| Random string IDs · Uniform spread | Fill-only | 0.85 | 0.8504 | Linear probing | 3.1611 / 1 / 13 / 59 | 17.0778 / 10 / 54 / 79 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 1.0909 / 1 / 2 / 3 | 1.2091 / 1 / 2 / 3 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 1.0909 / 1 / 2 / 3 | 1.2182 / 1 / 2 / 4 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 1.1689 / 1 / 2 / 3 | 1.4356 / 1 / 3 / 4 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 1.1689 / 1 / 2 / 5 | 1.4622 / 1 / 3 / 6 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 1.4194 / 1 / 3 / 5 | 1.6516 / 1 / 3 / 5 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 1.4194 / 1 / 3 / 8 | 2.3613 / 1 / 7 / 12 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 1.6132 / 1 / 3 / 5 | 1.9158 / 2 / 4 / 6 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 1.6132 / 1 / 4 / 17 | 3.0316 / 2 / 9 / 22 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 8.125 / 7 / 18 / 23 | 4.2 / 1 / 23 / 23 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.25 | 0.252 | Linear probing | 8.125 / 7 / 21 / 32 | 3.9562 / 1 / 31 / 31 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 12.7344 / 11 / 27 / 35 | 7.9594 / 4 / 23 / 26 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.5 | 0.5039 | Linear probing | 12.7344 / 9 / 35 / 56 | 11.7406 / 1 / 45 / 47 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 13.3258 / 12 / 28 / 39 | 12.0966 / 11 / 29 / 32 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.7 | 0.7008 | Linear probing | 13.3258 / 7 / 51 / 89 | 18.6854 / 5 / 67 / 85 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 13.7537 / 12 / 30 / 39 | 12.2759 / 12 / 27 / 31 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.85 | 0.8504 | Linear probing | 13.7537 / 8 / 45 / 83 | 28.0148 / 22 / 70 / 77 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 5.4818 / 5 / 11 / 13 | 2.7909 / 1 / 8 / 8 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 5.4818 / 5 / 13 / 22 | 2.3818 / 1 / 6 / 6 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 8.3244 / 7 / 19 / 22 | 1.7467 / 1 / 9 / 9 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 8.3244 / 6 / 23 / 34 | 5.9378 / 1 / 26 / 26 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 7.2032 / 7 / 15 / 18 | 3.8323 / 1 / 17 / 19 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 7.2032 / 5 / 26 / 44 | 5.7806 / 1 / 23 / 25 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 7.7789 / 7 / 18 / 23 | 6.0289 / 5 / 14 / 19 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 7.7789 / 5 / 25 / 39 | 10.0184 / 3 / 31 / 34 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 1.2563 / 1 / 2 / 5 | 1.2437 / 1 / 2 / 6 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.25 | 0.252 | Linear probing | 1.2563 / 1 / 2 / 7 | 1.3125 / 1 / 3 / 4 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 1.4094 / 1 / 3 / 4 | 1.7031 / 1 / 3 / 4 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.5 | 0.5039 | Linear probing | 1.4094 / 1 / 4 / 6 | 2.4156 / 2 / 8 / 11 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 2.0292 / 2 / 5 / 7 | 2.3236 / 2 / 5 / 8 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.7 | 0.7008 | Linear probing | 2.0292 / 1 / 6 / 19 | 4.8517 / 3 / 16 / 24 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 2.9667 / 2 / 7 / 11 | 3.5185 / 3 / 8 / 12 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.85 | 0.8504 | Linear probing | 2.9667 / 1 / 11 / 59 | 13.2204 / 6 / 54 / 78 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 1.2455 / 1 / 2 / 5 | 1.2455 / 1 / 2 / 6 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 1.2455 / 1 / 2 / 7 | 1.2091 / 1 / 2 / 4 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 1.2178 / 1 / 2 / 4 | 1.4267 / 1 / 3 / 5 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 1.2178 / 1 / 3 / 5 | 1.7378 / 1 / 4 / 9 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 1.3677 / 1 / 3 / 4 | 1.6 / 1 / 3 / 5 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 1.3677 / 1 / 3 / 7 | 2.2194 / 1 / 6 / 13 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 1.6105 / 1 / 3 / 5 | 1.9553 / 2 / 4 / 6 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 1.6105 / 1 / 4 / 10 | 3.5289 / 2 / 10 / 24 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 6.15 / 6 / 12 / 15 | 4.4 / 1 / 13 / 13 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.25 | 0.252 | Linear probing | 6.15 / 6 / 12 / 20 | 3.6875 / 1 / 10 / 15 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 9.0188 / 8 / 20 / 26 | 8.575 / 9 / 24 / 27 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.5 | 0.5039 | Linear probing | 9.0188 / 7 / 24 / 49 | 11.625 / 9 / 34 / 41 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 11.4966 / 10 / 25 / 35 | 7.8337 / 4 / 25 / 32 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.7 | 0.7008 | Linear probing | 11.4966 / 8 / 35 / 56 | 13.7955 / 9 / 46 / 55 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 15.0426 / 14 / 33 / 41 | 14.1222 / 11 / 36 / 42 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.85 | 0.8504 | Linear probing | 15.0426 / 9 / 55 / 99 | 23.4611 / 16 / 64 / 69 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 4.3909 / 4 / 9 / 11 | 1.0909 / 1 / 2 / 2 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 4.3909 / 4 / 9 / 11 | 1.3636 / 1 / 5 / 5 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 5.6533 / 5 / 13 / 17 | 3.0044 / 1 / 9 / 11 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 5.6533 / 5 / 14 / 18 | 3.7956 / 1 / 27 / 27 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 6.9226 / 6 / 18 / 23 | 4.3065 / 1 / 13 / 17 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 6.9226 / 5 / 19 / 33 | 5.3613 / 1 / 28 / 40 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 8.1421 / 7 / 18 / 27 | 5.3921 / 1 / 19 / 25 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 8.1421 / 6 / 25 / 61 | 13.0263 / 8 / 33 / 43 |

Positive p95 deltas mean Robin Hood hashing had the shorter lookup tail than linear probing for that slice.

| Key profile / preset | Workload | Requested load factor | Lower hit p95 | Hit p95 delta vs linear | Lower miss p95 | Miss p95 delta vs linear |
| --- | --- | ---: | --- | ---: | --- | ---: |
| Random string IDs · Uniform spread | Fill-only | 0.25 | Robin Hood hashing | 1 | Robin Hood hashing | 1 |
| Random string IDs · Uniform spread | Fill-only | 0.5 | Tie | 0 | Robin Hood hashing | 3 |
| Random string IDs · Uniform spread | Fill-only | 0.7 | Robin Hood hashing | 2 | Robin Hood hashing | 10 |
| Random string IDs · Uniform spread | Fill-only | 0.85 | Robin Hood hashing | 6 | Robin Hood hashing | 47 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | Tie | 0 | Tie | 0 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | Tie | 0 | Tie | 0 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | Tie | 0 | Robin Hood hashing | 4 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | Robin Hood hashing | 1 | Robin Hood hashing | 5 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.25 | Robin Hood hashing | 3 | Robin Hood hashing | 8 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.5 | Robin Hood hashing | 8 | Robin Hood hashing | 22 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.7 | Robin Hood hashing | 23 | Robin Hood hashing | 38 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.85 | Robin Hood hashing | 15 | Robin Hood hashing | 43 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | Robin Hood hashing | 2 | Linear probing | -2 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | Robin Hood hashing | 4 | Robin Hood hashing | 17 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | Robin Hood hashing | 11 | Robin Hood hashing | 6 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | Robin Hood hashing | 7 | Robin Hood hashing | 17 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.25 | Tie | 0 | Robin Hood hashing | 1 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.5 | Robin Hood hashing | 1 | Robin Hood hashing | 5 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.7 | Robin Hood hashing | 1 | Robin Hood hashing | 11 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.85 | Robin Hood hashing | 4 | Robin Hood hashing | 46 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | Tie | 0 | Tie | 0 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | Robin Hood hashing | 1 | Robin Hood hashing | 1 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | Tie | 0 | Robin Hood hashing | 3 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | Robin Hood hashing | 1 | Robin Hood hashing | 6 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.25 | Tie | 0 | Linear probing | -3 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.5 | Robin Hood hashing | 4 | Robin Hood hashing | 10 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.7 | Robin Hood hashing | 10 | Robin Hood hashing | 21 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.85 | Robin Hood hashing | 22 | Robin Hood hashing | 28 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | Tie | 0 | Robin Hood hashing | 3 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | Robin Hood hashing | 1 | Robin Hood hashing | 18 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | Robin Hood hashing | 1 | Robin Hood hashing | 15 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | Robin Hood hashing | 7 | Robin Hood hashing | 14 |

## Aggregate metrics

| Key profile / preset | Workload | Requested load factor | Remaining load factor | Strategy | Deleted entries | Avg insert probes | Avg delete probes | Avg successful lookup probes | Avg unsuccessful lookup probes | Avg probe distance | Probe-distance stddev | Max probe distance | Max cluster length | Avg swaps |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Random string IDs · Uniform spread | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 0 | 1.2125 | 0 | 1.2125 | 1.2875 | 0.2125 | 0.5048 | 2 | 12 | 1.2 |
| Random string IDs · Uniform spread | Fill-only | 0.25 | 0.252 | Linear probing | 0 | 1.2125 | 0 | 1.2125 | 1.425 | 0.2125 | 0.5851 | 4 | 12 | 0 |
| Random string IDs · Uniform spread | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 0 | 1.3781 | 0 | 1.3781 | 1.7688 | 0.3781 | 0.6644 | 3 | 10 | 5.4 |
| Random string IDs · Uniform spread | Fill-only | 0.5 | 0.5039 | Linear probing | 0 | 1.3781 | 0 | 1.3781 | 2.1594 | 0.3781 | 0.9173 | 7 | 10 | 0 |
| Random string IDs · Uniform spread | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 0 | 1.8944 | 0 | 1.8944 | 2.3551 | 0.8944 | 0.9785 | 4 | 22 | 32.4 |
| Random string IDs · Uniform spread | Fill-only | 0.7 | 0.7008 | Linear probing | 0 | 1.8944 | 0 | 1.8944 | 5.2944 | 0.8944 | 1.8409 | 15 | 22 | 0 |
| Random string IDs · Uniform spread | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 0 | 3.1611 | 0 | 3.1611 | 3.6704 | 2.1611 | 1.9355 | 9 | 78 | 106.8 |
| Random string IDs · Uniform spread | Fill-only | 0.85 | 0.8504 | Linear probing | 0 | 3.1611 | 0 | 3.1611 | 17.0778 | 2.1611 | 5.3505 | 58 | 78 | 0 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 10 | 1.2125 | 1.18 | 1.0909 | 1.2091 | 0.0909 | 0.3175 | 2 | 5 | 1.2 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 10 | 1.2125 | 1.14 | 1.0909 | 1.2182 | 0.0909 | 0.345 | 2 | 5 | 0 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 19 | 1.3781 | 1.3263 | 1.1689 | 1.4356 | 0.1689 | 0.4299 | 2 | 6 | 5.4 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 19 | 1.3781 | 1.4 | 1.1689 | 1.4622 | 0.1689 | 0.5232 | 4 | 6 | 0 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 27 | 1.8944 | 1.5333 | 1.4194 | 1.6516 | 0.4194 | 0.699 | 4 | 11 | 32.4 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 27 | 1.8944 | 1.6815 | 1.4194 | 2.3613 | 0.4194 | 0.9596 | 7 | 11 | 0 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 32 | 3.1611 | 2.3125 | 1.6132 | 1.9158 | 0.6132 | 0.8431 | 4 | 22 | 106.8 |
| Random string IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 32 | 3.1611 | 2.45 | 1.6132 | 3.0316 | 0.6132 | 1.5045 | 16 | 22 | 0 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 0 | 8.125 | 0 | 8.125 | 4.2 | 7.125 | 5.0569 | 22 | 32 | 5.2 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.25 | 0.252 | Linear probing | 0 | 8.125 | 0 | 8.125 | 3.9562 | 7.125 | 6.3045 | 31 | 32 | 0 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 0 | 12.7344 | 0 | 12.7344 | 7.9594 | 11.7344 | 7.9672 | 34 | 56 | 39.2 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.5 | 0.5039 | Linear probing | 0 | 12.7344 | 0 | 12.7344 | 11.7406 | 11.7344 | 11.3265 | 55 | 56 | 0 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 0 | 13.3258 | 0 | 13.3258 | 12.0966 | 12.3258 | 8.158 | 38 | 89 | 57.4 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.7 | 0.7008 | Linear probing | 0 | 13.3258 | 0 | 13.3258 | 18.6854 | 12.3258 | 16.5248 | 88 | 89 | 0 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 0 | 13.7537 | 0 | 13.7537 | 12.2759 | 12.7537 | 8.3916 | 38 | 86 | 59.4 |
| Random string IDs · Collision-focused hotspots | Fill-only | 0.85 | 0.8504 | Linear probing | 0 | 13.7537 | 0 | 13.7537 | 28.0148 | 12.7537 | 15.0589 | 82 | 86 | 0 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 10 | 8.125 | 6.92 | 5.4818 | 2.7909 | 4.4818 | 3.0799 | 12 | 22 | 5.2 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 10 | 8.125 | 6.46 | 5.4818 | 2.3818 | 4.4818 | 4.1093 | 21 | 22 | 0 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 19 | 12.7344 | 10.3263 | 8.3244 | 1.7467 | 7.3244 | 5.4297 | 21 | 34 | 39.2 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 19 | 12.7344 | 9.9368 | 8.3244 | 5.9378 | 7.3244 | 7.154 | 33 | 34 | 0 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 27 | 13.3258 | 10.2889 | 7.2032 | 3.8323 | 6.2032 | 4.3693 | 17 | 46 | 57.4 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 27 | 13.3258 | 10.563 | 7.2032 | 5.7806 | 6.2032 | 7.4877 | 43 | 46 | 0 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 32 | 13.7537 | 10.6375 | 7.7789 | 6.0289 | 6.7789 | 5.0834 | 22 | 43 | 59.4 |
| Random string IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 32 | 13.7537 | 8.7438 | 7.7789 | 10.0184 | 6.7789 | 7.4649 | 38 | 43 | 0 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 0 | 1.2563 | 0 | 1.2563 | 1.2437 | 0.2562 | 0.6447 | 4 | 7 | 1.6 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.25 | 0.252 | Linear probing | 0 | 1.2563 | 0 | 1.2563 | 1.3125 | 0.2562 | 0.7685 | 6 | 7 | 0 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 0 | 1.4094 | 0 | 1.4094 | 1.7031 | 0.4094 | 0.6552 | 3 | 11 | 7 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.5 | 0.5039 | Linear probing | 0 | 1.4094 | 0 | 1.4094 | 2.4156 | 0.4094 | 0.9509 | 5 | 11 | 0 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 0 | 2.0292 | 0 | 2.0292 | 2.3236 | 1.0292 | 1.2725 | 6 | 24 | 38.8 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.7 | 0.7008 | Linear probing | 0 | 2.0292 | 0 | 2.0292 | 4.8517 | 1.0292 | 2.3582 | 18 | 24 | 0 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 0 | 2.9667 | 0 | 2.9667 | 3.5185 | 1.9667 | 1.9395 | 10 | 80 | 96.8 |
| Sequential integer IDs · Uniform spread | Fill-only | 0.85 | 0.8504 | Linear probing | 0 | 2.9667 | 0 | 2.9667 | 13.2204 | 1.9667 | 5.0573 | 58 | 80 | 0 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 10 | 1.2563 | 1.14 | 1.2455 | 1.2455 | 0.2455 | 0.7031 | 4 | 7 | 1.6 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 10 | 1.2563 | 1.16 | 1.2455 | 1.2091 | 0.2455 | 0.8548 | 6 | 7 | 0 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 19 | 1.4094 | 1.3579 | 1.2178 | 1.4267 | 0.2178 | 0.4823 | 3 | 9 | 7 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 19 | 1.4094 | 1.3789 | 1.2178 | 1.7378 | 0.2178 | 0.6475 | 4 | 9 | 0 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 27 | 2.0292 | 1.7259 | 1.3677 | 1.6 | 0.3677 | 0.6478 | 3 | 13 | 38.8 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 27 | 2.0292 | 1.7259 | 1.3677 | 2.2194 | 0.3677 | 0.8982 | 6 | 13 | 0 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 32 | 2.9667 | 2.0438 | 1.6105 | 1.9553 | 0.6105 | 0.862 | 4 | 23 | 96.8 |
| Sequential integer IDs · Uniform spread | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 32 | 2.9667 | 2.1875 | 1.6105 | 3.5289 | 0.6105 | 1.3282 | 9 | 23 | 0 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.25 | 0.252 | Robin Hood hashing | 0 | 6.15 | 0 | 6.15 | 4.4 | 5.15 | 3.4609 | 14 | 32 | 0.2 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.25 | 0.252 | Linear probing | 0 | 6.15 | 0 | 6.15 | 3.6875 | 5.15 | 3.6094 | 19 | 32 | 0 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.5 | 0.5039 | Robin Hood hashing | 0 | 9.0188 | 0 | 9.0188 | 8.575 | 8.0188 | 5.5073 | 25 | 49 | 17.6 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.5 | 0.5039 | Linear probing | 0 | 9.0188 | 0 | 9.0188 | 11.625 | 8.0188 | 7.847 | 48 | 49 | 0 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.7 | 0.7008 | Robin Hood hashing | 0 | 11.4966 | 0 | 11.4966 | 7.8337 | 10.4966 | 7.1396 | 34 | 60 | 43.6 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.7 | 0.7008 | Linear probing | 0 | 11.4966 | 0 | 11.4966 | 13.7955 | 10.4966 | 10.5948 | 55 | 60 | 0 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.85 | 0.8504 | Robin Hood hashing | 0 | 15.0426 | 0 | 15.0426 | 14.1222 | 14.0426 | 8.9846 | 40 | 108 | 75.8 |
| Sequential integer IDs · Collision-focused hotspots | Fill-only | 0.85 | 0.8504 | Linear probing | 0 | 15.0426 | 0 | 15.0426 | 23.4611 | 14.0426 | 17.4059 | 98 | 108 | 0 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Robin Hood hashing | 10 | 6.15 | 5.46 | 4.3909 | 1.0909 | 3.3909 | 2.4461 | 10 | 11 | 0.2 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.25 | 0.1732 | Linear probing | 10 | 6.15 | 5.5 | 4.3909 | 1.3636 | 3.3909 | 2.4461 | 10 | 11 | 0 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Robin Hood hashing | 19 | 9.0188 | 7.6316 | 5.6533 | 3.0044 | 4.6533 | 3.6387 | 16 | 26 | 17.6 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.5 | 0.3543 | Linear probing | 19 | 9.0188 | 8.0947 | 5.6533 | 3.7956 | 4.6533 | 4.0227 | 17 | 26 | 0 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Robin Hood hashing | 27 | 11.4966 | 9.1778 | 6.9226 | 4.3065 | 5.9226 | 4.8073 | 22 | 42 | 43.6 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.7 | 0.4882 | Linear probing | 27 | 11.4966 | 10.1556 | 6.9226 | 5.3613 | 5.9226 | 5.9709 | 32 | 42 | 0 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Robin Hood hashing | 32 | 15.0426 | 11.2438 | 8.1421 | 5.3921 | 7.1421 | 5.0545 | 26 | 62 | 75.8 |
| Sequential integer IDs · Collision-focused hotspots | Delete-heavy (30.0% removals) | 0.85 | 0.5984 | Linear probing | 32 | 15.0426 | 10.0437 | 8.1421 | 13.0263 | 7.1421 | 8.0894 | 60 | 62 | 0 |

## Probe-distance histograms

Counts are aggregated across deterministic trials so the variance story is visible without digging through the raw CSV/JSON exports; for delete-heavy runs, the histograms are captured after the deterministic removal pass.

### Random string IDs

#### Uniform spread

##### Fill-only

###### Requested load factor 0.25 → remaining 0.252

32 starting entries per trial; 32 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 133 (83.1%) ██████████ | 137 (85.6%) ██████████ |
| 1 | 20 (12.5%) ██ | 14 (8.8%) █ |
| 2 | 7 (4.4%) █ | 8 (5.0%) █ |
| 4 | 0 (0.0%) | 1 (0.6%) █ |

###### Requested load factor 0.5 → remaining 0.5039

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

###### Requested load factor 0.7 → remaining 0.7008

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

###### Requested load factor 0.85 → remaining 0.8504

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

##### Delete-heavy (30.0% removals)

###### Requested load factor 0.25 → remaining 0.1732

32 starting entries per trial; 22 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 101 (91.8%) ███████████ | 102 (92.7%) ███████████ |
| 1 | 8 (7.3%) █ | 6 (5.5%) █ |
| 2 | 1 (0.9%) █ | 2 (1.8%) █ |

###### Requested load factor 0.5 → remaining 0.3543

64 starting entries per trial; 45 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 192 (85.3%) ██████████ | 197 (87.6%) ███████████ |
| 1 | 28 (12.4%) █ | 22 (9.8%) █ |
| 2 | 5 (2.2%) █ | 3 (1.3%) █ |
| 3 | 0 (0.0%) | 2 (0.9%) █ |
| 4 | 0 (0.0%) | 1 (0.4%) █ |

###### Requested load factor 0.7 → remaining 0.4882

89 starting entries per trial; 62 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 210 (67.7%) ████████ | 235 (75.8%) █████████ |
| 1 | 77 (24.8%) ███ | 48 (15.5%) ██ |
| 2 | 17 (5.5%) █ | 12 (3.9%) █ |
| 3 | 5 (1.6%) █ | 7 (2.3%) █ |
| 4 | 1 (0.3%) █ | 6 (1.9%) █ |
| 6 | 0 (0.0%) | 1 (0.3%) █ |
| 7 | 0 (0.0%) | 1 (0.3%) █ |

###### Requested load factor 0.85 → remaining 0.5984

108 starting entries per trial; 76 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 219 (57.6%) ███████ | 270 (71.0%) █████████ |
| 1 | 105 (27.6%) ███ | 63 (16.6%) ██ |
| 2 | 42 (11.1%) █ | 22 (5.8%) █ |
| 3 | 12 (3.2%) █ | 12 (3.2%) █ |
| 4 | 2 (0.5%) █ | 1 (0.3%) █ |
| 5 | 0 (0.0%) | 3 (0.8%) █ |
| 6 | 0 (0.0%) | 6 (1.6%) █ |
| 9 | 0 (0.0%) | 1 (0.3%) █ |
| 10 | 0 (0.0%) | 1 (0.3%) █ |
| 16 | 0 (0.0%) | 1 (0.3%) █ |

#### Collision-focused hotspots

##### Fill-only

###### Requested load factor 0.25 → remaining 0.252

32 starting entries per trial; 32 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 11 (6.9%) █ | 15 (9.4%) █ |
| 1 | 11 (6.9%) █ | 15 (9.4%) █ |
| 2 | 11 (6.9%) █ | 13 (8.1%) █ |
| 3 | 12 (7.5%) █ | 12 (7.5%) █ |
| 4 | 12 (7.5%) █ | 11 (6.9%) █ |
| 5 | 12 (7.5%) █ | 11 (6.9%) █ |
| 6 | 11 (6.9%) █ | 9 (5.6%) █ |
| 7 | 12 (7.5%) █ | 11 (6.9%) █ |
| 8 | 12 (7.5%) █ | 11 (6.9%) █ |
| 9 | 9 (5.6%) █ | 8 (5.0%) █ |
| 10 | 7 (4.4%) █ | 7 (4.4%) █ |
| 11 | 8 (5.0%) █ | 7 (4.4%) █ |
| 12 | 8 (5.0%) █ | 7 (4.4%) █ |
| 13 | 6 (3.8%) █ | 2 (1.2%) █ |
| 14 | 4 (2.5%) █ | 1 (0.6%) █ |
| 15 | 3 (1.9%) █ | 3 (1.9%) █ |
| 16 | 2 (1.2%) █ | 3 (1.9%) █ |
| 17 | 2 (1.2%) █ | 2 (1.2%) █ |
| 18 | 2 (1.2%) █ | 2 (1.2%) █ |
| 19 | 2 (1.2%) █ | 1 (0.6%) █ |
| 20 | 1 (0.6%) █ | 2 (1.2%) █ |
| 21 | 1 (0.6%) █ | 1 (0.6%) █ |
| 22 | 1 (0.6%) █ | 1 (0.6%) █ |
| 24 | 0 (0.0%) | 2 (1.2%) █ |
| 28 | 0 (0.0%) | 1 (0.6%) █ |
| 30 | 0 (0.0%) | 1 (0.6%) █ |
| 31 | 0 (0.0%) | 1 (0.6%) █ |

###### Requested load factor 0.5 → remaining 0.5039

64 starting entries per trial; 64 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 12 (3.8%) █ | 28 (8.8%) █ |
| 1 | 13 (4.1%) █ | 27 (8.4%) █ |
| 2 | 13 (4.1%) █ | 23 (7.2%) █ |
| 3 | 14 (4.4%) █ | 19 (5.9%) █ |
| 4 | 15 (4.7%) █ | 13 (4.1%) █ |
| 5 | 16 (5.0%) █ | 17 (5.3%) █ |
| 6 | 17 (5.3%) █ | 15 (4.7%) █ |
| 7 | 17 (5.3%) █ | 15 (4.7%) █ |
| 8 | 15 (4.7%) █ | 12 (3.8%) █ |
| 9 | 16 (5.0%) █ | 9 (2.8%) █ |
| 10 | 15 (4.7%) █ | 10 (3.1%) █ |
| 11 | 13 (4.1%) █ | 6 (1.9%) █ |
| 12 | 10 (3.1%) █ | 6 (1.9%) █ |
| 13 | 11 (3.4%) █ | 7 (2.2%) █ |
| 14 | 12 (3.8%) █ | 2 (0.6%) █ |
| 15 | 10 (3.1%) █ | 8 (2.5%) █ |
| 16 | 11 (3.4%) █ | 9 (2.8%) █ |
| 17 | 11 (3.4%) █ | 6 (1.9%) █ |
| 18 | 10 (3.1%) █ | 8 (2.5%) █ |
| 19 | 10 (3.1%) █ | 5 (1.6%) █ |
| 20 | 7 (2.2%) █ | 6 (1.9%) █ |
| 21 | 8 (2.5%) █ | 10 (3.1%) █ |
| 22 | 8 (2.5%) █ | 6 (1.9%) █ |
| 23 | 6 (1.9%) █ | 7 (2.2%) █ |
| 24 | 5 (1.6%) █ | 4 (1.2%) █ |
| 25 | 5 (1.6%) █ | 2 (0.6%) █ |
| 26 | 4 (1.2%) █ | 3 (0.9%) █ |
| 27 | 4 (1.2%) █ | 4 (1.2%) █ |
| 28 | 3 (0.9%) █ | 1 (0.3%) █ |
| 29 | 2 (0.6%) █ | 2 (0.6%) █ |
| 30 | 2 (0.6%) █ | 2 (0.6%) █ |
| 31 | 2 (0.6%) █ | 4 (1.2%) █ |
| 32 | 1 (0.3%) █ | 2 (0.6%) █ |
| 33 | 1 (0.3%) █ | 5 (1.6%) █ |
| 34 | 1 (0.3%) █ | 1 (0.3%) █ |
| 35 | 0 (0.0%) | 3 (0.9%) █ |
| 36 | 0 (0.0%) | 1 (0.3%) █ |
| 37 | 0 (0.0%) | 2 (0.6%) █ |
| 38 | 0 (0.0%) | 2 (0.6%) █ |
| 40 | 0 (0.0%) | 1 (0.3%) █ |
| 43 | 0 (0.0%) | 1 (0.3%) █ |
| 44 | 0 (0.0%) | 2 (0.6%) █ |
| 49 | 0 (0.0%) | 2 (0.6%) █ |
| 51 | 0 (0.0%) | 1 (0.3%) █ |
| 55 | 0 (0.0%) | 1 (0.3%) █ |

###### Requested load factor 0.7 → remaining 0.7008

89 starting entries per trial; 89 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 13 (2.9%) █ | 39 (8.8%) █ |
| 1 | 15 (3.4%) █ | 38 (8.5%) █ |
| 2 | 15 (3.4%) █ | 36 (8.1%) █ |
| 3 | 17 (3.8%) █ | 36 (8.1%) █ |
| 4 | 19 (4.3%) █ | 27 (6.1%) █ |
| 5 | 22 (4.9%) █ | 24 (5.4%) █ |
| 6 | 22 (4.9%) █ | 27 (6.1%) █ |
| 7 | 20 (4.5%) █ | 27 (6.1%) █ |
| 8 | 22 (4.9%) █ | 15 (3.4%) █ |
| 9 | 23 (5.2%) █ | 18 (4.0%) █ |
| 10 | 23 (5.2%) █ | 12 (2.7%) █ |
| 11 | 21 (4.7%) █ | 11 (2.5%) █ |
| 12 | 23 (5.2%) █ | 12 (2.7%) █ |
| 13 | 22 (4.9%) █ | 10 (2.2%) █ |
| 14 | 18 (4.0%) █ | 5 (1.1%) █ |
| 15 | 17 (3.8%) █ | 8 (1.8%) █ |
| 16 | 12 (2.7%) █ | 6 (1.4%) █ |
| 17 | 11 (2.5%) █ | 7 (1.6%) █ |
| 18 | 11 (2.5%) █ | 2 (0.4%) █ |
| 19 | 9 (2.0%) █ | 6 (1.4%) █ |
| 20 | 9 (2.0%) █ | 2 (0.4%) █ |
| 21 | 9 (2.0%) █ | 1 (0.2%) █ |
| 22 | 9 (2.0%) █ | 1 (0.2%) █ |
| 23 | 9 (2.0%) █ | 3 (0.7%) █ |
| 24 | 9 (2.0%) █ | 4 (0.9%) █ |
| 25 | 9 (2.0%) █ | 6 (1.4%) █ |
| 26 | 8 (1.8%) █ | 1 (0.2%) █ |
| 27 | 6 (1.4%) █ | 0 (0.0%) |
| 28 | 5 (1.1%) █ | 6 (1.4%) █ |
| 29 | 4 (0.9%) █ | 2 (0.4%) █ |
| 30 | 3 (0.7%) █ | 4 (0.9%) █ |
| 31 | 2 (0.4%) █ | 2 (0.4%) █ |
| 32 | 2 (0.4%) █ | 2 (0.4%) █ |
| 33 | 1 (0.2%) █ | 0 (0.0%) |
| 34 | 1 (0.2%) █ | 1 (0.2%) █ |
| 35 | 1 (0.2%) █ | 2 (0.4%) █ |
| 36 | 1 (0.2%) █ | 2 (0.4%) █ |
| 37 | 1 (0.2%) █ | 1 (0.2%) █ |
| 38 | 1 (0.2%) █ | 2 (0.4%) █ |
| 39 | 0 (0.0%) | 1 (0.2%) █ |
| 40 | 0 (0.0%) | 3 (0.7%) █ |
| 42 | 0 (0.0%) | 3 (0.7%) █ |
| 43 | 0 (0.0%) | 2 (0.4%) █ |
| 44 | 0 (0.0%) | 3 (0.7%) █ |
| 45 | 0 (0.0%) | 1 (0.2%) █ |
| 46 | 0 (0.0%) | 1 (0.2%) █ |
| 50 | 0 (0.0%) | 1 (0.2%) █ |
| 51 | 0 (0.0%) | 1 (0.2%) █ |
| 52 | 0 (0.0%) | 1 (0.2%) █ |
| 53 | 0 (0.0%) | 1 (0.2%) █ |
| 57 | 0 (0.0%) | 1 (0.2%) █ |
| 58 | 0 (0.0%) | 1 (0.2%) █ |
| 59 | 0 (0.0%) | 1 (0.2%) █ |
| 64 | 0 (0.0%) | 2 (0.4%) █ |
| 66 | 0 (0.0%) | 1 (0.2%) █ |
| 68 | 0 (0.0%) | 2 (0.4%) █ |
| 70 | 0 (0.0%) | 1 (0.2%) █ |
| 71 | 0 (0.0%) | 1 (0.2%) █ |
| 72 | 0 (0.0%) | 1 (0.2%) █ |
| 75 | 0 (0.0%) | 3 (0.7%) █ |
| 76 | 0 (0.0%) | 1 (0.2%) █ |
| 78 | 0 (0.0%) | 1 (0.2%) █ |
| 82 | 0 (0.0%) | 1 (0.2%) █ |
| 85 | 0 (0.0%) | 1 (0.2%) █ |
| 88 | 0 (0.0%) | 1 (0.2%) █ |

###### Requested load factor 0.85 → remaining 0.8504

108 starting entries per trial; 108 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 15 (2.8%) █ | 44 (8.2%) █ |
| 1 | 18 (3.3%) █ | 38 (7.0%) █ |
| 2 | 18 (3.3%) █ | 34 (6.3%) █ |
| 3 | 20 (3.7%) █ | 36 (6.7%) █ |
| 4 | 22 (4.1%) █ | 38 (7.0%) █ |
| 5 | 23 (4.3%) █ | 31 (5.7%) █ |
| 6 | 26 (4.8%) █ | 30 (5.6%) █ |
| 7 | 26 (4.8%) █ | 28 (5.2%) █ |
| 8 | 27 (5.0%) █ | 24 (4.4%) █ |
| 9 | 25 (4.6%) █ | 21 (3.9%) █ |
| 10 | 25 (4.6%) █ | 17 (3.1%) █ |
| 11 | 26 (4.8%) █ | 16 (3.0%) █ |
| 12 | 26 (4.8%) █ | 12 (2.2%) █ |
| 13 | 23 (4.3%) █ | 13 (2.4%) █ |
| 14 | 22 (4.1%) █ | 8 (1.5%) █ |
| 15 | 21 (3.9%) █ | 10 (1.8%) █ |
| 16 | 19 (3.5%) █ | 5 (0.9%) █ |
| 17 | 17 (3.1%) █ | 4 (0.7%) █ |
| 18 | 14 (2.6%) █ | 9 (1.7%) █ |
| 19 | 14 (2.6%) █ | 6 (1.1%) █ |
| 20 | 13 (2.4%) █ | 2 (0.4%) █ |
| 21 | 9 (1.7%) █ | 4 (0.7%) █ |
| 22 | 9 (1.7%) █ | 6 (1.1%) █ |
| 23 | 9 (1.7%) █ | 7 (1.3%) █ |
| 24 | 9 (1.7%) █ | 6 (1.1%) █ |
| 25 | 9 (1.7%) █ | 6 (1.1%) █ |
| 26 | 10 (1.8%) █ | 7 (1.3%) █ |
| 27 | 9 (1.7%) █ | 3 (0.6%) █ |
| 28 | 7 (1.3%) █ | 3 (0.6%) █ |
| 29 | 7 (1.3%) █ | 5 (0.9%) █ |
| 30 | 6 (1.1%) █ | 3 (0.6%) █ |
| 31 | 4 (0.7%) █ | 4 (0.7%) █ |
| 32 | 3 (0.6%) █ | 2 (0.4%) █ |
| 33 | 3 (0.6%) █ | 3 (0.6%) █ |
| 34 | 2 (0.4%) █ | 4 (0.7%) █ |
| 35 | 1 (0.2%) █ | 3 (0.6%) █ |
| 36 | 1 (0.2%) █ | 2 (0.4%) █ |
| 37 | 1 (0.2%) █ | 5 (0.9%) █ |
| 38 | 1 (0.2%) █ | 0 (0.0%) |
| 39 | 0 (0.0%) | 2 (0.4%) █ |
| 40 | 0 (0.0%) | 4 (0.7%) █ |
| 41 | 0 (0.0%) | 2 (0.4%) █ |
| 42 | 0 (0.0%) | 2 (0.4%) █ |
| 43 | 0 (0.0%) | 3 (0.6%) █ |
| 44 | 0 (0.0%) | 3 (0.6%) █ |
| 45 | 0 (0.0%) | 2 (0.4%) █ |
| 46 | 0 (0.0%) | 3 (0.6%) █ |
| 47 | 0 (0.0%) | 1 (0.2%) █ |
| 48 | 0 (0.0%) | 2 (0.4%) █ |
| 49 | 0 (0.0%) | 1 (0.2%) █ |
| 50 | 0 (0.0%) | 1 (0.2%) █ |
| 52 | 0 (0.0%) | 1 (0.2%) █ |
| 63 | 0 (0.0%) | 1 (0.2%) █ |
| 64 | 0 (0.0%) | 1 (0.2%) █ |
| 65 | 0 (0.0%) | 1 (0.2%) █ |
| 66 | 0 (0.0%) | 1 (0.2%) █ |
| 67 | 0 (0.0%) | 1 (0.2%) █ |
| 68 | 0 (0.0%) | 2 (0.4%) █ |
| 69 | 0 (0.0%) | 1 (0.2%) █ |
| 74 | 0 (0.0%) | 1 (0.2%) █ |
| 75 | 0 (0.0%) | 1 (0.2%) █ |
| 76 | 0 (0.0%) | 1 (0.2%) █ |
| 80 | 0 (0.0%) | 1 (0.2%) █ |
| 82 | 0 (0.0%) | 2 (0.4%) █ |

##### Delete-heavy (30.0% removals)

###### Requested load factor 0.25 → remaining 0.1732

32 starting entries per trial; 22 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 11 (10.0%) █ | 15 (13.6%) ██ |
| 1 | 11 (10.0%) █ | 15 (13.6%) ██ |
| 2 | 12 (10.9%) █ | 12 (10.9%) █ |
| 3 | 13 (11.8%) █ | 11 (10.0%) █ |
| 4 | 12 (10.9%) █ | 11 (10.0%) █ |
| 5 | 11 (10.0%) █ | 11 (10.0%) █ |
| 6 | 10 (9.1%) █ | 9 (8.2%) █ |
| 7 | 10 (9.1%) █ | 7 (6.4%) █ |
| 8 | 7 (6.4%) █ | 4 (3.6%) █ |
| 9 | 5 (4.5%) █ | 2 (1.8%) █ |
| 10 | 4 (3.6%) █ | 4 (3.6%) █ |
| 11 | 3 (2.7%) █ | 3 (2.7%) █ |
| 12 | 1 (0.9%) █ | 1 (0.9%) █ |
| 13 | 0 (0.0%) | 1 (0.9%) █ |
| 14 | 0 (0.0%) | 1 (0.9%) █ |
| 16 | 0 (0.0%) | 1 (0.9%) █ |
| 20 | 0 (0.0%) | 1 (0.9%) █ |
| 21 | 0 (0.0%) | 1 (0.9%) █ |

###### Requested load factor 0.5 → remaining 0.3543

64 starting entries per trial; 45 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 16 (7.1%) █ | 29 (12.9%) ██ |
| 1 | 16 (7.1%) █ | 27 (12.0%) █ |
| 2 | 16 (7.1%) █ | 22 (9.8%) █ |
| 3 | 19 (8.4%) █ | 15 (6.7%) █ |
| 4 | 17 (7.6%) █ | 11 (4.9%) █ |
| 5 | 16 (7.1%) █ | 11 (4.9%) █ |
| 6 | 13 (5.8%) █ | 10 (4.4%) █ |
| 7 | 16 (7.1%) █ | 12 (5.3%) █ |
| 8 | 16 (7.1%) █ | 11 (4.9%) █ |
| 9 | 12 (5.3%) █ | 11 (4.9%) █ |
| 10 | 10 (4.4%) █ | 5 (2.2%) █ |
| 11 | 9 (4.0%) █ | 5 (2.2%) █ |
| 12 | 7 (3.1%) █ | 7 (3.1%) █ |
| 13 | 6 (2.7%) █ | 7 (3.1%) █ |
| 14 | 5 (2.2%) █ | 6 (2.7%) █ |
| 15 | 6 (2.7%) █ | 3 (1.3%) █ |
| 16 | 6 (2.7%) █ | 5 (2.2%) █ |
| 17 | 6 (2.7%) █ | 5 (2.2%) █ |
| 18 | 4 (1.8%) █ | 1 (0.4%) █ |
| 19 | 4 (1.8%) █ | 4 (1.8%) █ |
| 20 | 3 (1.3%) █ | 3 (1.3%) █ |
| 21 | 2 (0.9%) █ | 2 (0.9%) █ |
| 22 | 0 (0.0%) | 3 (1.3%) █ |
| 23 | 0 (0.0%) | 2 (0.9%) █ |
| 24 | 0 (0.0%) | 1 (0.4%) █ |
| 25 | 0 (0.0%) | 1 (0.4%) █ |
| 26 | 0 (0.0%) | 2 (0.9%) █ |
| 28 | 0 (0.0%) | 2 (0.9%) █ |
| 30 | 0 (0.0%) | 1 (0.4%) █ |
| 33 | 0 (0.0%) | 1 (0.4%) █ |

###### Requested load factor 0.7 → remaining 0.4882

89 starting entries per trial; 62 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 24 (7.7%) █ | 39 (12.6%) ██ |
| 1 | 25 (8.1%) █ | 39 (12.6%) ██ |
| 2 | 25 (8.1%) █ | 33 (10.7%) █ |
| 3 | 28 (9.0%) █ | 35 (11.3%) █ |
| 4 | 26 (8.4%) █ | 26 (8.4%) █ |
| 5 | 24 (7.7%) █ | 24 (7.7%) █ |
| 6 | 24 (7.7%) █ | 21 (6.8%) █ |
| 7 | 23 (7.4%) █ | 17 (5.5%) █ |
| 8 | 19 (6.1%) █ | 12 (3.9%) █ |
| 9 | 18 (5.8%) █ | 6 (1.9%) █ |
| 10 | 17 (5.5%) █ | 8 (2.6%) █ |
| 11 | 13 (4.2%) █ | 6 (1.9%) █ |
| 12 | 12 (3.9%) █ | 3 (1.0%) █ |
| 13 | 10 (3.2%) █ | 4 (1.3%) █ |
| 14 | 8 (2.6%) █ | 5 (1.6%) █ |
| 15 | 6 (1.9%) █ | 2 (0.7%) █ |
| 16 | 4 (1.3%) █ | 3 (1.0%) █ |
| 17 | 4 (1.3%) █ | 3 (1.0%) █ |
| 18 | 0 (0.0%) | 3 (1.0%) █ |
| 20 | 0 (0.0%) | 1 (0.3%) █ |
| 22 | 0 (0.0%) | 1 (0.3%) █ |
| 23 | 0 (0.0%) | 2 (0.7%) █ |
| 24 | 0 (0.0%) | 1 (0.3%) █ |
| 25 | 0 (0.0%) | 1 (0.3%) █ |
| 26 | 0 (0.0%) | 2 (0.7%) █ |
| 27 | 0 (0.0%) | 1 (0.3%) █ |
| 28 | 0 (0.0%) | 4 (1.3%) █ |
| 29 | 0 (0.0%) | 2 (0.7%) █ |
| 30 | 0 (0.0%) | 1 (0.3%) █ |
| 33 | 0 (0.0%) | 1 (0.3%) █ |
| 37 | 0 (0.0%) | 1 (0.3%) █ |
| 38 | 0 (0.0%) | 1 (0.3%) █ |
| 40 | 0 (0.0%) | 1 (0.3%) █ |
| 43 | 0 (0.0%) | 1 (0.3%) █ |

###### Requested load factor 0.85 → remaining 0.5984

108 starting entries per trial; 76 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 26 (6.8%) █ | 43 (11.3%) █ |
| 1 | 29 (7.6%) █ | 42 (11.1%) █ |
| 2 | 31 (8.2%) █ | 38 (10.0%) █ |
| 3 | 33 (8.7%) █ | 36 (9.5%) █ |
| 4 | 32 (8.4%) █ | 31 (8.2%) █ |
| 5 | 32 (8.4%) █ | 29 (7.6%) █ |
| 6 | 30 (7.9%) █ | 28 (7.4%) █ |
| 7 | 25 (6.6%) █ | 21 (5.5%) █ |
| 8 | 22 (5.8%) █ | 18 (4.7%) █ |
| 9 | 17 (4.5%) █ | 14 (3.7%) █ |
| 10 | 19 (5.0%) █ | 9 (2.4%) █ |
| 11 | 15 (4.0%) █ | 7 (1.8%) █ |
| 12 | 11 (2.9%) █ | 4 (1.1%) █ |
| 13 | 9 (2.4%) █ | 5 (1.3%) █ |
| 14 | 10 (2.6%) █ | 6 (1.6%) █ |
| 15 | 9 (2.4%) █ | 3 (0.8%) █ |
| 16 | 8 (2.1%) █ | 4 (1.1%) █ |
| 17 | 7 (1.8%) █ | 5 (1.3%) █ |
| 18 | 6 (1.6%) █ | 5 (1.3%) █ |
| 19 | 4 (1.1%) █ | 3 (0.8%) █ |
| 20 | 2 (0.5%) █ | 2 (0.5%) █ |
| 21 | 2 (0.5%) █ | 2 (0.5%) █ |
| 22 | 1 (0.3%) █ | 2 (0.5%) █ |
| 23 | 0 (0.0%) | 2 (0.5%) █ |
| 24 | 0 (0.0%) | 3 (0.8%) █ |
| 25 | 0 (0.0%) | 3 (0.8%) █ |
| 26 | 0 (0.0%) | 2 (0.5%) █ |
| 27 | 0 (0.0%) | 1 (0.3%) █ |
| 29 | 0 (0.0%) | 1 (0.3%) █ |
| 30 | 0 (0.0%) | 4 (1.1%) █ |
| 31 | 0 (0.0%) | 2 (0.5%) █ |
| 35 | 0 (0.0%) | 1 (0.3%) █ |
| 36 | 0 (0.0%) | 2 (0.5%) █ |
| 37 | 0 (0.0%) | 1 (0.3%) █ |
| 38 | 0 (0.0%) | 1 (0.3%) █ |

### Sequential integer IDs

#### Uniform spread

##### Fill-only

###### Requested load factor 0.25 → remaining 0.252

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

###### Requested load factor 0.5 → remaining 0.5039

64 starting entries per trial; 64 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 216 (67.5%) ████████ | 248 (77.5%) █████████ |
| 1 | 80 (25.0%) ███ | 43 (13.4%) ██ |
| 2 | 21 (6.6%) █ | 12 (3.8%) █ |
| 3 | 3 (0.9%) █ | 8 (2.5%) █ |
| 4 | 0 (0.0%) | 5 (1.6%) █ |
| 5 | 0 (0.0%) | 4 (1.2%) █ |

###### Requested load factor 0.7 → remaining 0.7008

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

###### Requested load factor 0.85 → remaining 0.8504

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

##### Delete-heavy (30.0% removals)

###### Requested load factor 0.25 → remaining 0.1732

32 starting entries per trial; 22 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 93 (84.5%) ██████████ | 96 (87.3%) ██████████ |
| 1 | 12 (10.9%) █ | 9 (8.2%) █ |
| 2 | 2 (1.8%) █ | 2 (1.8%) █ |
| 3 | 1 (0.9%) █ | 1 (0.9%) █ |
| 4 | 2 (1.8%) █ | 0 (0.0%) |
| 5 | 0 (0.0%) | 1 (0.9%) █ |
| 6 | 0 (0.0%) | 1 (0.9%) █ |

###### Requested load factor 0.5 → remaining 0.3543

64 starting entries per trial; 45 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 182 (80.9%) ██████████ | 195 (86.7%) ██████████ |
| 1 | 38 (16.9%) ██ | 18 (8.0%) █ |
| 2 | 4 (1.8%) █ | 7 (3.1%) █ |
| 3 | 1 (0.4%) █ | 3 (1.3%) █ |
| 4 | 0 (0.0%) | 2 (0.9%) █ |

###### Requested load factor 0.7 → remaining 0.4882

89 starting entries per trial; 62 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 222 (71.6%) █████████ | 245 (79.0%) █████████ |
| 1 | 65 (21.0%) ███ | 40 (12.9%) ██ |
| 2 | 20 (6.5%) █ | 10 (3.2%) █ |
| 3 | 3 (1.0%) █ | 11 (3.5%) █ |
| 4 | 0 (0.0%) | 1 (0.3%) █ |
| 5 | 0 (0.0%) | 1 (0.3%) █ |
| 6 | 0 (0.0%) | 2 (0.7%) █ |

###### Requested load factor 0.85 → remaining 0.5984

108 starting entries per trial; 76 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 222 (58.4%) ███████ | 271 (71.3%) █████████ |
| 1 | 102 (26.8%) ███ | 57 (15.0%) ██ |
| 2 | 42 (11.1%) █ | 24 (6.3%) █ |
| 3 | 10 (2.6%) █ | 11 (2.9%) █ |
| 4 | 4 (1.1%) █ | 5 (1.3%) █ |
| 5 | 0 (0.0%) | 6 (1.6%) █ |
| 6 | 0 (0.0%) | 2 (0.5%) █ |
| 7 | 0 (0.0%) | 1 (0.3%) █ |
| 8 | 0 (0.0%) | 2 (0.5%) █ |
| 9 | 0 (0.0%) | 1 (0.3%) █ |

#### Collision-focused hotspots

##### Fill-only

###### Requested load factor 0.25 → remaining 0.252

32 starting entries per trial; 32 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 14 (8.8%) █ | 15 (9.4%) █ |
| 1 | 15 (9.4%) █ | 15 (9.4%) █ |
| 2 | 15 (9.4%) █ | 15 (9.4%) █ |
| 3 | 15 (9.4%) █ | 15 (9.4%) █ |
| 4 | 15 (9.4%) █ | 15 (9.4%) █ |
| 5 | 15 (9.4%) █ | 15 (9.4%) █ |
| 6 | 14 (8.8%) █ | 14 (8.8%) █ |
| 7 | 14 (8.8%) █ | 13 (8.1%) █ |
| 8 | 12 (7.5%) █ | 12 (7.5%) █ |
| 9 | 10 (6.2%) █ | 10 (6.2%) █ |
| 10 | 9 (5.6%) █ | 9 (5.6%) █ |
| 11 | 6 (3.8%) █ | 6 (3.8%) █ |
| 12 | 4 (2.5%) █ | 3 (1.9%) █ |
| 13 | 1 (0.6%) █ | 1 (0.6%) █ |
| 14 | 1 (0.6%) █ | 1 (0.6%) █ |
| 19 | 0 (0.0%) | 1 (0.6%) █ |

###### Requested load factor 0.5 → remaining 0.5039

64 starting entries per trial; 64 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 17 (5.3%) █ | 30 (9.4%) █ |
| 1 | 18 (5.6%) █ | 27 (8.4%) █ |
| 2 | 19 (5.9%) █ | 27 (8.4%) █ |
| 3 | 20 (6.2%) █ | 27 (8.4%) █ |
| 4 | 21 (6.6%) █ | 22 (6.9%) █ |
| 5 | 23 (7.2%) █ | 24 (7.5%) █ |
| 6 | 24 (7.5%) █ | 16 (5.0%) █ |
| 7 | 24 (7.5%) █ | 21 (6.6%) █ |
| 8 | 22 (6.9%) █ | 14 (4.4%) █ |
| 9 | 21 (6.6%) █ | 12 (3.8%) █ |
| 10 | 18 (5.6%) █ | 10 (3.1%) █ |
| 11 | 18 (5.6%) █ | 12 (3.8%) █ |
| 12 | 13 (4.1%) █ | 6 (1.9%) █ |
| 13 | 12 (3.8%) █ | 9 (2.8%) █ |
| 14 | 9 (2.8%) █ | 10 (3.1%) █ |
| 15 | 6 (1.9%) █ | 6 (1.9%) █ |
| 16 | 6 (1.9%) █ | 5 (1.6%) █ |
| 17 | 5 (1.6%) █ | 6 (1.9%) █ |
| 18 | 5 (1.6%) █ | 4 (1.2%) █ |
| 19 | 5 (1.6%) █ | 1 (0.3%) █ |
| 20 | 5 (1.6%) █ | 4 (1.2%) █ |
| 21 | 3 (0.9%) █ | 6 (1.9%) █ |
| 22 | 2 (0.6%) █ | 3 (0.9%) █ |
| 23 | 2 (0.6%) █ | 3 (0.9%) █ |
| 24 | 1 (0.3%) █ | 2 (0.6%) █ |
| 25 | 1 (0.3%) █ | 1 (0.3%) █ |
| 26 | 0 (0.0%) | 2 (0.6%) █ |
| 27 | 0 (0.0%) | 1 (0.3%) █ |
| 29 | 0 (0.0%) | 2 (0.6%) █ |
| 30 | 0 (0.0%) | 2 (0.6%) █ |
| 31 | 0 (0.0%) | 1 (0.3%) █ |
| 34 | 0 (0.0%) | 1 (0.3%) █ |
| 42 | 0 (0.0%) | 1 (0.3%) █ |
| 43 | 0 (0.0%) | 1 (0.3%) █ |
| 48 | 0 (0.0%) | 1 (0.3%) █ |

###### Requested load factor 0.7 → remaining 0.7008

89 starting entries per trial; 89 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 15 (3.4%) █ | 38 (8.5%) █ |
| 1 | 18 (4.0%) █ | 35 (7.9%) █ |
| 2 | 20 (4.5%) █ | 33 (7.4%) █ |
| 3 | 22 (4.9%) █ | 28 (6.3%) █ |
| 4 | 23 (5.2%) █ | 31 (7.0%) █ |
| 5 | 23 (5.2%) █ | 26 (5.8%) █ |
| 6 | 24 (5.4%) █ | 18 (4.0%) █ |
| 7 | 26 (5.8%) █ | 21 (4.7%) █ |
| 8 | 26 (5.8%) █ | 17 (3.8%) █ |
| 9 | 27 (6.1%) █ | 16 (3.6%) █ |
| 10 | 27 (6.1%) █ | 8 (1.8%) █ |
| 11 | 23 (5.2%) █ | 16 (3.6%) █ |
| 12 | 21 (4.7%) █ | 13 (2.9%) █ |
| 13 | 21 (4.7%) █ | 13 (2.9%) █ |
| 14 | 20 (4.5%) █ | 14 (3.1%) █ |
| 15 | 15 (3.4%) █ | 11 (2.5%) █ |
| 16 | 13 (2.9%) █ | 12 (2.7%) █ |
| 17 | 13 (2.9%) █ | 11 (2.5%) █ |
| 18 | 7 (1.6%) █ | 9 (2.0%) █ |
| 19 | 7 (1.6%) █ | 7 (1.6%) █ |
| 20 | 8 (1.8%) █ | 10 (2.2%) █ |
| 21 | 8 (1.8%) █ | 5 (1.1%) █ |
| 22 | 6 (1.4%) █ | 2 (0.4%) █ |
| 23 | 7 (1.6%) █ | 4 (0.9%) █ |
| 24 | 5 (1.1%) █ | 4 (0.9%) █ |
| 25 | 3 (0.7%) █ | 1 (0.2%) █ |
| 26 | 2 (0.4%) █ | 1 (0.2%) █ |
| 27 | 2 (0.4%) █ | 4 (0.9%) █ |
| 28 | 2 (0.4%) █ | 1 (0.2%) █ |
| 29 | 2 (0.4%) █ | 5 (1.1%) █ |
| 30 | 2 (0.4%) █ | 4 (0.9%) █ |
| 31 | 2 (0.4%) █ | 3 (0.7%) █ |
| 32 | 2 (0.4%) █ | 0 (0.0%) |
| 33 | 2 (0.4%) █ | 1 (0.2%) █ |
| 34 | 1 (0.2%) █ | 1 (0.2%) █ |
| 35 | 0 (0.0%) | 2 (0.4%) █ |
| 37 | 0 (0.0%) | 3 (0.7%) █ |
| 38 | 0 (0.0%) | 2 (0.4%) █ |
| 39 | 0 (0.0%) | 2 (0.4%) █ |
| 41 | 0 (0.0%) | 1 (0.2%) █ |
| 42 | 0 (0.0%) | 2 (0.4%) █ |
| 43 | 0 (0.0%) | 1 (0.2%) █ |
| 44 | 0 (0.0%) | 1 (0.2%) █ |
| 45 | 0 (0.0%) | 2 (0.4%) █ |
| 46 | 0 (0.0%) | 2 (0.4%) █ |
| 47 | 0 (0.0%) | 1 (0.2%) █ |
| 48 | 0 (0.0%) | 1 (0.2%) █ |
| 53 | 0 (0.0%) | 1 (0.2%) █ |
| 55 | 0 (0.0%) | 1 (0.2%) █ |

###### Requested load factor 0.85 → remaining 0.8504

108 starting entries per trial; 108 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 13 (2.4%) █ | 44 (8.2%) █ |
| 1 | 13 (2.4%) █ | 39 (7.2%) █ |
| 2 | 15 (2.8%) █ | 37 (6.9%) █ |
| 3 | 19 (3.5%) █ | 34 (6.3%) █ |
| 4 | 20 (3.7%) █ | 31 (5.7%) █ |
| 5 | 20 (3.7%) █ | 23 (4.3%) █ |
| 6 | 21 (3.9%) █ | 25 (4.6%) █ |
| 7 | 22 (4.1%) █ | 21 (3.9%) █ |
| 8 | 25 (4.6%) █ | 25 (4.6%) █ |
| 9 | 25 (4.6%) █ | 30 (5.6%) █ |
| 10 | 23 (4.3%) █ | 19 (3.5%) █ |
| 11 | 23 (4.3%) █ | 19 (3.5%) █ |
| 12 | 25 (4.6%) █ | 14 (2.6%) █ |
| 13 | 21 (3.9%) █ | 11 (2.0%) █ |
| 14 | 22 (4.1%) █ | 10 (1.8%) █ |
| 15 | 25 (4.6%) █ | 11 (2.0%) █ |
| 16 | 22 (4.1%) █ | 9 (1.7%) █ |
| 17 | 20 (3.7%) █ | 9 (1.7%) █ |
| 18 | 17 (3.1%) █ | 5 (0.9%) █ |
| 19 | 17 (3.1%) █ | 2 (0.4%) █ |
| 20 | 13 (2.4%) █ | 4 (0.7%) █ |
| 21 | 10 (1.8%) █ | 8 (1.5%) █ |
| 22 | 11 (2.0%) █ | 4 (0.7%) █ |
| 23 | 10 (1.8%) █ | 8 (1.5%) █ |
| 24 | 9 (1.7%) █ | 4 (0.7%) █ |
| 25 | 10 (1.8%) █ | 1 (0.2%) █ |
| 26 | 8 (1.5%) █ | 9 (1.7%) █ |
| 27 | 7 (1.3%) █ | 5 (0.9%) █ |
| 28 | 8 (1.5%) █ | 4 (0.7%) █ |
| 29 | 6 (1.1%) █ | 4 (0.7%) █ |
| 30 | 6 (1.1%) █ | 3 (0.6%) █ |
| 31 | 6 (1.1%) █ | 3 (0.6%) █ |
| 32 | 6 (1.1%) █ | 5 (0.9%) █ |
| 33 | 5 (0.9%) █ | 0 (0.0%) |
| 34 | 4 (0.7%) █ | 0 (0.0%) |
| 35 | 4 (0.7%) █ | 1 (0.2%) █ |
| 36 | 3 (0.6%) █ | 1 (0.2%) █ |
| 37 | 3 (0.6%) █ | 4 (0.7%) █ |
| 38 | 1 (0.2%) █ | 3 (0.6%) █ |
| 39 | 1 (0.2%) █ | 0 (0.0%) |
| 40 | 1 (0.2%) █ | 2 (0.4%) █ |
| 41 | 0 (0.0%) | 5 (0.9%) █ |
| 43 | 0 (0.0%) | 2 (0.4%) █ |
| 45 | 0 (0.0%) | 3 (0.6%) █ |
| 46 | 0 (0.0%) | 1 (0.2%) █ |
| 48 | 0 (0.0%) | 1 (0.2%) █ |
| 49 | 0 (0.0%) | 3 (0.6%) █ |
| 50 | 0 (0.0%) | 2 (0.4%) █ |
| 51 | 0 (0.0%) | 1 (0.2%) █ |
| 52 | 0 (0.0%) | 1 (0.2%) █ |
| 53 | 0 (0.0%) | 2 (0.4%) █ |
| 54 | 0 (0.0%) | 2 (0.4%) █ |
| 55 | 0 (0.0%) | 1 (0.2%) █ |
| 56 | 0 (0.0%) | 2 (0.4%) █ |
| 59 | 0 (0.0%) | 3 (0.6%) █ |
| 60 | 0 (0.0%) | 1 (0.2%) █ |
| 61 | 0 (0.0%) | 1 (0.2%) █ |
| 63 | 0 (0.0%) | 1 (0.2%) █ |
| 64 | 0 (0.0%) | 1 (0.2%) █ |
| 67 | 0 (0.0%) | 1 (0.2%) █ |
| 69 | 0 (0.0%) | 1 (0.2%) █ |
| 70 | 0 (0.0%) | 1 (0.2%) █ |
| 71 | 0 (0.0%) | 1 (0.2%) █ |
| 72 | 0 (0.0%) | 3 (0.6%) █ |
| 73 | 0 (0.0%) | 1 (0.2%) █ |
| 74 | 0 (0.0%) | 1 (0.2%) █ |
| 78 | 0 (0.0%) | 1 (0.2%) █ |
| 81 | 0 (0.0%) | 1 (0.2%) █ |
| 83 | 0 (0.0%) | 2 (0.4%) █ |
| 93 | 0 (0.0%) | 1 (0.2%) █ |
| 96 | 0 (0.0%) | 1 (0.2%) █ |
| 98 | 0 (0.0%) | 1 (0.2%) █ |

##### Delete-heavy (30.0% removals)

###### Requested load factor 0.25 → remaining 0.1732

32 starting entries per trial; 22 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 15 (13.6%) ██ | 15 (13.6%) ██ |
| 1 | 15 (13.6%) ██ | 15 (13.6%) ██ |
| 2 | 15 (13.6%) ██ | 15 (13.6%) ██ |
| 3 | 15 (13.6%) ██ | 15 (13.6%) ██ |
| 4 | 14 (12.7%) ██ | 14 (12.7%) ██ |
| 5 | 12 (10.9%) █ | 12 (10.9%) █ |
| 6 | 10 (9.1%) █ | 10 (9.1%) █ |
| 7 | 8 (7.3%) █ | 8 (7.3%) █ |
| 8 | 4 (3.6%) █ | 4 (3.6%) █ |
| 9 | 1 (0.9%) █ | 1 (0.9%) █ |
| 10 | 1 (0.9%) █ | 1 (0.9%) █ |

###### Requested load factor 0.5 → remaining 0.3543

64 starting entries per trial; 45 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 25 (11.1%) █ | 29 (12.9%) ██ |
| 1 | 25 (11.1%) █ | 28 (12.4%) █ |
| 2 | 25 (11.1%) █ | 27 (12.0%) █ |
| 3 | 24 (10.7%) █ | 23 (10.2%) █ |
| 4 | 24 (10.7%) █ | 24 (10.7%) █ |
| 5 | 21 (9.3%) █ | 16 (7.1%) █ |
| 6 | 21 (9.3%) █ | 18 (8.0%) █ |
| 7 | 15 (6.7%) █ | 11 (4.9%) █ |
| 8 | 13 (5.8%) █ | 10 (4.4%) █ |
| 9 | 8 (3.6%) █ | 10 (4.4%) █ |
| 10 | 6 (2.7%) █ | 7 (3.1%) █ |
| 11 | 4 (1.8%) █ | 6 (2.7%) █ |
| 12 | 4 (1.8%) █ | 3 (1.3%) █ |
| 13 | 4 (1.8%) █ | 3 (1.3%) █ |
| 14 | 3 (1.3%) █ | 3 (1.3%) █ |
| 15 | 2 (0.9%) █ | 2 (0.9%) █ |
| 16 | 1 (0.4%) █ | 3 (1.3%) █ |
| 17 | 0 (0.0%) | 2 (0.9%) █ |

###### Requested load factor 0.7 → remaining 0.4882

89 starting entries per trial; 62 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 26 (8.4%) █ | 39 (12.6%) ██ |
| 1 | 28 (9.0%) █ | 34 (11.0%) █ |
| 2 | 28 (9.0%) █ | 31 (10.0%) █ |
| 3 | 30 (9.7%) █ | 34 (11.0%) █ |
| 4 | 29 (9.3%) █ | 27 (8.7%) █ |
| 5 | 30 (9.7%) █ | 16 (5.2%) █ |
| 6 | 28 (9.0%) █ | 22 (7.1%) █ |
| 7 | 21 (6.8%) █ | 18 (5.8%) █ |
| 8 | 16 (5.2%) █ | 10 (3.2%) █ |
| 9 | 16 (5.2%) █ | 15 (4.8%) █ |
| 10 | 13 (4.2%) █ | 11 (3.5%) █ |
| 11 | 9 (2.9%) █ | 10 (3.2%) █ |
| 12 | 5 (1.6%) █ | 9 (2.9%) █ |
| 13 | 4 (1.3%) █ | 5 (1.6%) █ |
| 14 | 5 (1.6%) █ | 5 (1.6%) █ |
| 15 | 3 (1.0%) █ | 4 (1.3%) █ |
| 16 | 3 (1.0%) █ | 2 (0.7%) █ |
| 17 | 3 (1.0%) █ | 2 (0.7%) █ |
| 18 | 3 (1.0%) █ | 2 (0.7%) █ |
| 19 | 4 (1.3%) █ | 0 (0.0%) |
| 20 | 3 (1.0%) █ | 3 (1.0%) █ |
| 21 | 2 (0.7%) █ | 0 (0.0%) |
| 22 | 1 (0.3%) █ | 0 (0.0%) |
| 23 | 0 (0.0%) | 2 (0.7%) █ |
| 24 | 0 (0.0%) | 1 (0.3%) █ |
| 25 | 0 (0.0%) | 1 (0.3%) █ |
| 26 | 0 (0.0%) | 2 (0.7%) █ |
| 27 | 0 (0.0%) | 1 (0.3%) █ |
| 28 | 0 (0.0%) | 2 (0.7%) █ |
| 30 | 0 (0.0%) | 1 (0.3%) █ |
| 32 | 0 (0.0%) | 1 (0.3%) █ |

###### Requested load factor 0.85 → remaining 0.5984

108 starting entries per trial; 76 remain after the workload across 5 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 20 (5.3%) █ | 44 (11.6%) █ |
| 1 | 24 (6.3%) █ | 39 (10.3%) █ |
| 2 | 25 (6.6%) █ | 36 (9.5%) █ |
| 3 | 28 (7.4%) █ | 38 (10.0%) █ |
| 4 | 32 (8.4%) █ | 29 (7.6%) █ |
| 5 | 33 (8.7%) █ | 32 (8.4%) █ |
| 6 | 33 (8.7%) █ | 25 (6.6%) █ |
| 7 | 31 (8.2%) █ | 19 (5.0%) █ |
| 8 | 28 (7.4%) █ | 12 (3.2%) █ |
| 9 | 23 (6.0%) █ | 10 (2.6%) █ |
| 10 | 22 (5.8%) █ | 6 (1.6%) █ |
| 11 | 16 (4.2%) █ | 10 (2.6%) █ |
| 12 | 14 (3.7%) █ | 11 (2.9%) █ |
| 13 | 9 (2.4%) █ | 8 (2.1%) █ |
| 14 | 8 (2.1%) █ | 9 (2.4%) █ |
| 15 | 8 (2.1%) █ | 6 (1.6%) █ |
| 16 | 4 (1.1%) █ | 6 (1.6%) █ |
| 17 | 4 (1.1%) █ | 4 (1.1%) █ |
| 18 | 4 (1.1%) █ | 2 (0.5%) █ |
| 19 | 4 (1.1%) █ | 4 (1.1%) █ |
| 20 | 2 (0.5%) █ | 3 (0.8%) █ |
| 21 | 2 (0.5%) █ | 1 (0.3%) █ |
| 22 | 2 (0.5%) █ | 1 (0.3%) █ |
| 23 | 1 (0.3%) █ | 4 (1.1%) █ |
| 24 | 1 (0.3%) █ | 3 (0.8%) █ |
| 25 | 1 (0.3%) █ | 1 (0.3%) █ |
| 26 | 1 (0.3%) █ | 6 (1.6%) █ |
| 27 | 0 (0.0%) | 2 (0.5%) █ |
| 29 | 0 (0.0%) | 2 (0.5%) █ |
| 30 | 0 (0.0%) | 2 (0.5%) █ |
| 31 | 0 (0.0%) | 1 (0.3%) █ |
| 34 | 0 (0.0%) | 1 (0.3%) █ |
| 50 | 0 (0.0%) | 1 (0.3%) █ |
| 51 | 0 (0.0%) | 1 (0.3%) █ |
| 60 | 0 (0.0%) | 1 (0.3%) █ |

## Unsuccessful-lookup histograms

Counts are aggregated across deterministic trials after each workload finishes, so failed-search cost is visible alongside the resident probe-distance story.

### Random string IDs

#### Uniform spread

##### Fill-only

###### Requested load factor 0.25 → remaining 0.252

32 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 32 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 119 (74.4%) █████████ | 119 (74.4%) █████████ |
| 2 | 38 (23.8%) ███ | 28 (17.5%) ██ |
| 3 | 1 (0.6%) █ | 9 (5.6%) █ |
| 4 | 2 (1.2%) █ | 2 (1.2%) █ |
| 9 | 0 (0.0%) | 2 (1.2%) █ |

###### Requested load factor 0.5 → remaining 0.5039

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

###### Requested load factor 0.7 → remaining 0.7008

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

###### Requested load factor 0.85 → remaining 0.8504

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

##### Delete-heavy (30.0% removals)

###### Requested load factor 0.25 → remaining 0.1732

22 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 22 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 90 (81.8%) ██████████ | 91 (82.7%) ██████████ |
| 2 | 17 (15.4%) ██ | 15 (13.6%) ██ |
| 3 | 3 (2.7%) █ | 3 (2.7%) █ |
| 4 | 0 (0.0%) | 1 (0.9%) █ |

###### Requested load factor 0.5 → remaining 0.3543

45 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 45 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 143 (63.6%) ████████ | 155 (68.9%) ████████ |
| 2 | 68 (30.2%) ████ | 45 (20.0%) ██ |
| 3 | 12 (5.3%) █ | 20 (8.9%) █ |
| 4 | 2 (0.9%) █ | 3 (1.3%) █ |
| 6 | 0 (0.0%) | 2 (0.9%) █ |

###### Requested load factor 0.7 → remaining 0.4882

62 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 62 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 165 (53.2%) ██████ | 157 (50.6%) ██████ |
| 2 | 101 (32.6%) ████ | 53 (17.1%) ██ |
| 3 | 35 (11.3%) █ | 42 (13.6%) ██ |
| 4 | 5 (1.6%) █ | 18 (5.8%) █ |
| 5 | 4 (1.3%) █ | 14 (4.5%) █ |
| 6 | 0 (0.0%) | 8 (2.6%) █ |
| 7 | 0 (0.0%) | 5 (1.6%) █ |
| 8 | 0 (0.0%) | 6 (1.9%) █ |
| 9 | 0 (0.0%) | 3 (1.0%) █ |
| 10 | 0 (0.0%) | 2 (0.7%) █ |
| 11 | 0 (0.0%) | 1 (0.3%) █ |
| 12 | 0 (0.0%) | 1 (0.3%) █ |

###### Requested load factor 0.85 → remaining 0.5984

76 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 76 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 157 (41.3%) █████ | 155 (40.8%) █████ |
| 2 | 136 (35.8%) ████ | 75 (19.7%) ██ |
| 3 | 56 (14.7%) ██ | 35 (9.2%) █ |
| 4 | 25 (6.6%) █ | 33 (8.7%) █ |
| 5 | 5 (1.3%) █ | 25 (6.6%) █ |
| 6 | 1 (0.3%) █ | 16 (4.2%) █ |
| 7 | 0 (0.0%) | 15 (4.0%) █ |
| 8 | 0 (0.0%) | 6 (1.6%) █ |
| 9 | 0 (0.0%) | 6 (1.6%) █ |
| 10 | 0 (0.0%) | 4 (1.1%) █ |
| 11 | 0 (0.0%) | 2 (0.5%) █ |
| 12 | 0 (0.0%) | 4 (1.1%) █ |
| 13 | 0 (0.0%) | 1 (0.3%) █ |
| 18 | 0 (0.0%) | 1 (0.3%) █ |
| 19 | 0 (0.0%) | 1 (0.3%) █ |
| 22 | 0 (0.0%) | 1 (0.3%) █ |

#### Collision-focused hotspots

##### Fill-only

###### Requested load factor 0.25 → remaining 0.252

32 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 32 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 120 (75.0%) █████████ | 114 (71.2%) █████████ |
| 3 | 0 (0.0%) | 10 (6.2%) █ |
| 5 | 13 (8.1%) █ | 19 (11.9%) █ |
| 12 | 0 (0.0%) | 7 (4.4%) █ |
| 13 | 8 (5.0%) █ | 0 (0.0%) |
| 17 | 9 (5.6%) █ | 0 (0.0%) |
| 23 | 10 (6.2%) █ | 0 (0.0%) |
| 31 | 0 (0.0%) | 10 (6.2%) █ |

###### Requested load factor 0.5 → remaining 0.5039

64 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 64 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 115 (35.9%) ████ | 187 (58.4%) ███████ |
| 2 | 9 (2.8%) █ | 0 (0.0%) |
| 3 | 7 (2.2%) █ | 0 (0.0%) |
| 4 | 33 (10.3%) █ | 0 (0.0%) |
| 5 | 9 (2.8%) █ | 9 (2.8%) █ |
| 6 | 9 (2.8%) █ | 0 (0.0%) |
| 7 | 13 (4.1%) █ | 8 (2.5%) █ |
| 9 | 0 (0.0%) | 12 (3.8%) █ |
| 10 | 9 (2.8%) █ | 0 (0.0%) |
| 11 | 7 (2.2%) █ | 0 (0.0%) |
| 12 | 26 (8.1%) █ | 0 (0.0%) |
| 14 | 14 (4.4%) █ | 0 (0.0%) |
| 15 | 11 (3.4%) █ | 11 (3.4%) █ |
| 16 | 0 (0.0%) | 10 (3.1%) █ |
| 17 | 10 (3.1%) █ | 0 (0.0%) |
| 19 | 10 (3.1%) █ | 0 (0.0%) |
| 20 | 14 (4.4%) █ | 0 (0.0%) |
| 23 | 11 (3.4%) █ | 0 (0.0%) |
| 26 | 13 (4.1%) █ | 12 (3.8%) █ |
| 30 | 0 (0.0%) | 15 (4.7%) █ |
| 35 | 0 (0.0%) | 9 (2.8%) █ |
| 38 | 0 (0.0%) | 12 (3.8%) █ |
| 39 | 0 (0.0%) | 12 (3.8%) █ |
| 42 | 0 (0.0%) | 6 (1.9%) █ |
| 45 | 0 (0.0%) | 8 (2.5%) █ |
| 47 | 0 (0.0%) | 9 (2.8%) █ |

###### Requested load factor 0.7 → remaining 0.7008

89 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 89 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 92 (20.7%) ██ | 180 (40.5%) █████ |
| 3 | 0 (0.0%) | 23 (5.2%) █ |
| 4 | 14 (3.1%) █ | 16 (3.6%) █ |
| 5 | 15 (3.4%) █ | 18 (4.0%) █ |
| 6 | 28 (6.3%) █ | 13 (2.9%) █ |
| 7 | 28 (6.3%) █ | 0 (0.0%) |
| 9 | 4 (0.9%) █ | 6 (1.4%) █ |
| 10 | 24 (5.4%) █ | 0 (0.0%) |
| 11 | 19 (4.3%) █ | 0 (0.0%) |
| 12 | 23 (5.2%) █ | 0 (0.0%) |
| 13 | 36 (8.1%) █ | 0 (0.0%) |
| 15 | 19 (4.3%) █ | 0 (0.0%) |
| 16 | 21 (4.7%) █ | 15 (3.4%) █ |
| 17 | 18 (4.0%) █ | 6 (1.4%) █ |
| 18 | 11 (2.5%) █ | 0 (0.0%) |
| 20 | 0 (0.0%) | 15 (3.4%) █ |
| 21 | 0 (0.0%) | 9 (2.0%) █ |
| 22 | 10 (2.2%) █ | 0 (0.0%) |
| 23 | 12 (2.7%) █ | 0 (0.0%) |
| 24 | 25 (5.6%) █ | 4 (0.9%) █ |
| 27 | 15 (3.4%) █ | 22 (4.9%) █ |
| 29 | 11 (2.5%) █ | 0 (0.0%) |
| 30 | 9 (2.0%) █ | 28 (6.3%) █ |
| 32 | 11 (2.5%) █ | 0 (0.0%) |
| 41 | 0 (0.0%) | 10 (2.2%) █ |
| 52 | 0 (0.0%) | 19 (4.3%) █ |
| 53 | 0 (0.0%) | 10 (2.2%) █ |
| 58 | 0 (0.0%) | 9 (2.0%) █ |
| 62 | 0 (0.0%) | 11 (2.5%) █ |
| 67 | 0 (0.0%) | 11 (2.5%) █ |
| 70 | 0 (0.0%) | 10 (2.2%) █ |
| 85 | 0 (0.0%) | 10 (2.2%) █ |

###### Requested load factor 0.85 → remaining 0.8504

108 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 108 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 91 (16.9%) ██ | 84 (15.6%) ██ |
| 2 | 12 (2.2%) █ | 0 (0.0%) |
| 3 | 9 (1.7%) █ | 11 (2.0%) █ |
| 4 | 15 (2.8%) █ | 26 (4.8%) █ |
| 5 | 10 (1.8%) █ | 16 (3.0%) █ |
| 6 | 13 (2.4%) █ | 20 (3.7%) █ |
| 7 | 21 (3.9%) █ | 0 (0.0%) |
| 8 | 50 (9.3%) █ | 0 (0.0%) |
| 9 | 0 (0.0%) | 12 (2.2%) █ |
| 10 | 28 (5.2%) █ | 0 (0.0%) |
| 11 | 14 (2.6%) █ | 0 (0.0%) |
| 12 | 12 (2.2%) █ | 9 (1.7%) █ |
| 13 | 23 (4.3%) █ | 16 (3.0%) █ |
| 14 | 0 (0.0%) | 21 (3.9%) █ |
| 15 | 22 (4.1%) █ | 0 (0.0%) |
| 16 | 44 (8.2%) █ | 0 (0.0%) |
| 17 | 39 (7.2%) █ | 7 (1.3%) █ |
| 18 | 36 (6.7%) █ | 19 (3.5%) █ |
| 19 | 26 (4.8%) █ | 10 (1.8%) █ |
| 21 | 0 (0.0%) | 8 (1.5%) █ |
| 22 | 8 (1.5%) █ | 14 (2.6%) █ |
| 24 | 0 (0.0%) | 34 (6.3%) █ |
| 25 | 11 (2.0%) █ | 0 (0.0%) |
| 26 | 9 (1.7%) █ | 0 (0.0%) |
| 27 | 24 (4.4%) █ | 0 (0.0%) |
| 30 | 10 (1.8%) █ | 0 (0.0%) |
| 31 | 13 (2.4%) █ | 0 (0.0%) |
| 36 | 0 (0.0%) | 42 (7.8%) █ |
| 41 | 0 (0.0%) | 15 (2.8%) █ |
| 44 | 0 (0.0%) | 22 (4.1%) █ |
| 46 | 0 (0.0%) | 18 (3.3%) █ |
| 47 | 0 (0.0%) | 11 (2.0%) █ |
| 49 | 0 (0.0%) | 29 (5.4%) █ |
| 56 | 0 (0.0%) | 8 (1.5%) █ |
| 57 | 0 (0.0%) | 16 (3.0%) █ |
| 59 | 0 (0.0%) | 9 (1.7%) █ |
| 60 | 0 (0.0%) | 13 (2.4%) █ |
| 64 | 0 (0.0%) | 7 (1.3%) █ |
| 66 | 0 (0.0%) | 14 (2.6%) █ |
| 70 | 0 (0.0%) | 13 (2.4%) █ |
| 77 | 0 (0.0%) | 16 (3.0%) █ |

##### Delete-heavy (30.0% removals)

###### Requested load factor 0.25 → remaining 0.1732

22 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 22 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 75 (68.2%) ████████ | 65 (59.1%) ███████ |
| 2 | 0 (0.0%) | 10 (9.1%) █ |
| 4 | 12 (10.9%) █ | 10 (9.1%) █ |
| 5 | 0 (0.0%) | 13 (11.8%) █ |
| 6 | 0 (0.0%) | 12 (10.9%) █ |
| 8 | 23 (20.9%) ███ | 0 (0.0%) |

###### Requested load factor 0.5 → remaining 0.3543

45 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 45 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 192 (85.3%) ██████████ | 136 (60.4%) ███████ |
| 3 | 12 (5.3%) █ | 0 (0.0%) |
| 5 | 0 (0.0%) | 9 (4.0%) █ |
| 6 | 8 (3.6%) █ | 20 (8.9%) █ |
| 7 | 0 (0.0%) | 10 (4.4%) █ |
| 9 | 13 (5.8%) █ | 0 (0.0%) |
| 16 | 0 (0.0%) | 30 (13.3%) ██ |
| 21 | 0 (0.0%) | 7 (3.1%) █ |
| 26 | 0 (0.0%) | 13 (5.8%) █ |

###### Requested load factor 0.7 → remaining 0.4882

62 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 62 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 188 (60.7%) ███████ | 186 (60.0%) ███████ |
| 2 | 0 (0.0%) | 12 (3.9%) █ |
| 3 | 35 (11.3%) █ | 15 (4.8%) █ |
| 5 | 28 (9.0%) █ | 0 (0.0%) |
| 6 | 18 (5.8%) █ | 15 (4.8%) █ |
| 10 | 0 (0.0%) | 18 (5.8%) █ |
| 13 | 14 (4.5%) █ | 0 (0.0%) |
| 14 | 0 (0.0%) | 8 (2.6%) █ |
| 15 | 7 (2.3%) █ | 0 (0.0%) |
| 17 | 10 (3.2%) █ | 0 (0.0%) |
| 18 | 0 (0.0%) | 23 (7.4%) █ |
| 19 | 10 (3.2%) █ | 0 (0.0%) |
| 20 | 0 (0.0%) | 8 (2.6%) █ |
| 21 | 0 (0.0%) | 7 (2.3%) █ |
| 23 | 0 (0.0%) | 8 (2.6%) █ |
| 25 | 0 (0.0%) | 10 (3.2%) █ |

###### Requested load factor 0.85 → remaining 0.5984

76 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 76 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 80 (21.1%) ███ | 173 (45.5%) █████ |
| 2 | 32 (8.4%) █ | 10 (2.6%) █ |
| 3 | 41 (10.8%) █ | 11 (2.9%) █ |
| 4 | 25 (6.6%) █ | 14 (3.7%) █ |
| 5 | 44 (11.6%) █ | 22 (5.8%) █ |
| 6 | 24 (6.3%) █ | 0 (0.0%) |
| 7 | 8 (2.1%) █ | 0 (0.0%) |
| 8 | 40 (10.5%) █ | 0 (0.0%) |
| 9 | 0 (0.0%) | 5 (1.3%) █ |
| 11 | 12 (3.2%) █ | 0 (0.0%) |
| 12 | 23 (6.0%) █ | 0 (0.0%) |
| 13 | 9 (2.4%) █ | 0 (0.0%) |
| 14 | 23 (6.0%) █ | 10 (2.6%) █ |
| 15 | 0 (0.0%) | 10 (2.6%) █ |
| 16 | 8 (2.1%) █ | 19 (5.0%) █ |
| 19 | 11 (2.9%) █ | 21 (5.5%) █ |
| 22 | 0 (0.0%) | 10 (2.6%) █ |
| 23 | 0 (0.0%) | 12 (3.2%) █ |
| 27 | 0 (0.0%) | 22 (5.8%) █ |
| 30 | 0 (0.0%) | 16 (4.2%) █ |
| 31 | 0 (0.0%) | 12 (3.2%) █ |
| 33 | 0 (0.0%) | 7 (1.8%) █ |
| 34 | 0 (0.0%) | 6 (1.6%) █ |

### Sequential integer IDs

#### Uniform spread

##### Fill-only

###### Requested load factor 0.25 → remaining 0.252

32 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 32 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 127 (79.4%) ██████████ | 125 (78.1%) █████████ |
| 2 | 30 (18.8%) ██ | 24 (15.0%) ██ |
| 3 | 2 (1.2%) █ | 7 (4.4%) █ |
| 4 | 0 (0.0%) | 4 (2.5%) █ |
| 6 | 1 (0.6%) █ | 0 (0.0%) |

###### Requested load factor 0.5 → remaining 0.5039

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

###### Requested load factor 0.7 → remaining 0.7008

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

###### Requested load factor 0.85 → remaining 0.8504

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

##### Delete-heavy (30.0% removals)

###### Requested load factor 0.25 → remaining 0.1732

22 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 22 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 93 (84.5%) ██████████ | 95 (86.4%) ██████████ |
| 2 | 12 (10.9%) █ | 10 (9.1%) █ |
| 3 | 2 (1.8%) █ | 2 (1.8%) █ |
| 4 | 2 (1.8%) █ | 3 (2.7%) █ |
| 6 | 1 (0.9%) █ | 0 (0.0%) |

###### Requested load factor 0.5 → remaining 0.3543

45 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 45 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 149 (66.2%) ████████ | 142 (63.1%) ████████ |
| 2 | 58 (25.8%) ███ | 44 (19.6%) ██ |
| 3 | 17 (7.6%) █ | 19 (8.4%) █ |
| 4 | 0 (0.0%) | 9 (4.0%) █ |
| 5 | 1 (0.4%) █ | 4 (1.8%) █ |
| 6 | 0 (0.0%) | 4 (1.8%) █ |
| 7 | 0 (0.0%) | 1 (0.4%) █ |
| 8 | 0 (0.0%) | 1 (0.4%) █ |
| 9 | 0 (0.0%) | 1 (0.4%) █ |

###### Requested load factor 0.7 → remaining 0.4882

62 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 62 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 167 (53.9%) ██████ | 166 (53.5%) ██████ |
| 2 | 110 (35.5%) ████ | 59 (19.0%) ██ |
| 3 | 25 (8.1%) █ | 38 (12.3%) █ |
| 4 | 6 (1.9%) █ | 16 (5.2%) █ |
| 5 | 2 (0.7%) █ | 7 (2.3%) █ |
| 6 | 0 (0.0%) | 9 (2.9%) █ |
| 7 | 0 (0.0%) | 5 (1.6%) █ |
| 8 | 0 (0.0%) | 2 (0.7%) █ |
| 9 | 0 (0.0%) | 1 (0.3%) █ |
| 10 | 0 (0.0%) | 3 (1.0%) █ |
| 11 | 0 (0.0%) | 2 (0.7%) █ |
| 12 | 0 (0.0%) | 1 (0.3%) █ |
| 13 | 0 (0.0%) | 1 (0.3%) █ |

###### Requested load factor 0.85 → remaining 0.5984

76 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 76 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 162 (42.6%) █████ | 136 (35.8%) ████ |
| 2 | 118 (31.1%) ████ | 67 (17.6%) ██ |
| 3 | 63 (16.6%) ██ | 47 (12.4%) █ |
| 4 | 30 (7.9%) █ | 32 (8.4%) █ |
| 5 | 6 (1.6%) █ | 23 (6.0%) █ |
| 6 | 1 (0.3%) █ | 19 (5.0%) █ |
| 7 | 0 (0.0%) | 9 (2.4%) █ |
| 8 | 0 (0.0%) | 20 (5.3%) █ |
| 9 | 0 (0.0%) | 4 (1.1%) █ |
| 10 | 0 (0.0%) | 5 (1.3%) █ |
| 11 | 0 (0.0%) | 6 (1.6%) █ |
| 12 | 0 (0.0%) | 3 (0.8%) █ |
| 14 | 0 (0.0%) | 1 (0.3%) █ |
| 15 | 0 (0.0%) | 1 (0.3%) █ |
| 16 | 0 (0.0%) | 1 (0.3%) █ |
| 17 | 0 (0.0%) | 1 (0.3%) █ |
| 18 | 0 (0.0%) | 1 (0.3%) █ |
| 19 | 0 (0.0%) | 2 (0.5%) █ |
| 20 | 0 (0.0%) | 1 (0.3%) █ |
| 24 | 0 (0.0%) | 1 (0.3%) █ |

#### Collision-focused hotspots

##### Fill-only

###### Requested load factor 0.25 → remaining 0.252

32 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 32 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 107 (66.9%) ████████ | 80 (50.0%) ██████ |
| 3 | 0 (0.0%) | 12 (7.5%) █ |
| 4 | 0 (0.0%) | 37 (23.1%) ███ |
| 8 | 0 (0.0%) | 12 (7.5%) █ |
| 10 | 18 (11.2%) █ | 11 (6.9%) █ |
| 11 | 14 (8.8%) █ | 0 (0.0%) |
| 12 | 10 (6.2%) █ | 0 (0.0%) |
| 13 | 11 (6.9%) █ | 0 (0.0%) |
| 15 | 0 (0.0%) | 8 (5.0%) █ |

###### Requested load factor 0.5 → remaining 0.5039

64 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 64 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 113 (35.3%) ████ | 137 (42.8%) █████ |
| 2 | 6 (1.9%) █ | 18 (5.6%) █ |
| 4 | 3 (0.9%) █ | 0 (0.0%) |
| 6 | 12 (3.8%) █ | 0 (0.0%) |
| 7 | 13 (4.1%) █ | 0 (0.0%) |
| 8 | 7 (2.2%) █ | 0 (0.0%) |
| 9 | 27 (8.4%) █ | 21 (6.6%) █ |
| 10 | 14 (4.4%) █ | 6 (1.9%) █ |
| 11 | 13 (4.1%) █ | 0 (0.0%) |
| 12 | 26 (8.1%) █ | 11 (3.4%) █ |
| 13 | 35 (10.9%) █ | 0 (0.0%) |
| 14 | 9 (2.8%) █ | 12 (3.8%) █ |
| 15 | 8 (2.5%) █ | 13 (4.1%) █ |
| 16 | 0 (0.0%) | 9 (2.8%) █ |
| 19 | 0 (0.0%) | 4 (1.2%) █ |
| 20 | 0 (0.0%) | 7 (2.2%) █ |
| 22 | 0 (0.0%) | 8 (2.5%) █ |
| 23 | 0 (0.0%) | 14 (4.4%) █ |
| 24 | 23 (7.2%) █ | 0 (0.0%) |
| 26 | 0 (0.0%) | 7 (2.2%) █ |
| 27 | 11 (3.4%) █ | 0 (0.0%) |
| 28 | 0 (0.0%) | 15 (4.7%) █ |
| 32 | 0 (0.0%) | 8 (2.5%) █ |
| 34 | 0 (0.0%) | 14 (4.4%) █ |
| 36 | 0 (0.0%) | 9 (2.8%) █ |
| 41 | 0 (0.0%) | 7 (2.2%) █ |

###### Requested load factor 0.7 → remaining 0.7008

89 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 89 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 163 (36.6%) ████ | 151 (33.9%) ████ |
| 2 | 39 (8.8%) █ | 7 (1.6%) █ |
| 3 | 7 (1.6%) █ | 7 (1.6%) █ |
| 4 | 33 (7.4%) █ | 29 (6.5%) █ |
| 5 | 14 (3.1%) █ | 0 (0.0%) |
| 8 | 0 (0.0%) | 6 (1.4%) █ |
| 9 | 17 (3.8%) █ | 24 (5.4%) █ |
| 10 | 12 (2.7%) █ | 14 (3.1%) █ |
| 11 | 22 (4.9%) █ | 24 (5.4%) █ |
| 12 | 17 (3.8%) █ | 19 (4.3%) █ |
| 13 | 23 (5.2%) █ | 6 (1.4%) █ |
| 14 | 23 (5.2%) █ | 0 (0.0%) |
| 15 | 7 (1.6%) █ | 0 (0.0%) |
| 16 | 0 (0.0%) | 11 (2.5%) █ |
| 17 | 24 (5.4%) █ | 0 (0.0%) |
| 18 | 0 (0.0%) | 14 (3.1%) █ |
| 20 | 0 (0.0%) | 18 (4.0%) █ |
| 21 | 6 (1.4%) █ | 10 (2.2%) █ |
| 22 | 0 (0.0%) | 3 (0.7%) █ |
| 23 | 5 (1.1%) █ | 0 (0.0%) |
| 25 | 16 (3.6%) █ | 0 (0.0%) |
| 27 | 0 (0.0%) | 10 (2.2%) █ |
| 28 | 0 (0.0%) | 25 (5.6%) █ |
| 30 | 8 (1.8%) █ | 13 (2.9%) █ |
| 32 | 9 (2.0%) █ | 0 (0.0%) |
| 39 | 0 (0.0%) | 9 (2.0%) █ |
| 41 | 0 (0.0%) | 13 (2.9%) █ |
| 45 | 0 (0.0%) | 7 (1.6%) █ |
| 46 | 0 (0.0%) | 15 (3.4%) █ |
| 55 | 0 (0.0%) | 10 (2.2%) █ |

###### Requested load factor 0.85 → remaining 0.8504

108 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 108 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 87 (16.1%) ██ | 80 (14.8%) ██ |
| 2 | 22 (4.1%) █ | 0 (0.0%) |
| 4 | 18 (3.3%) █ | 9 (1.7%) █ |
| 5 | 30 (5.6%) █ | 37 (6.9%) █ |
| 6 | 5 (0.9%) █ | 0 (0.0%) |
| 7 | 6 (1.1%) █ | 21 (3.9%) █ |
| 8 | 10 (1.8%) █ | 26 (4.8%) █ |
| 9 | 23 (4.3%) █ | 17 (3.1%) █ |
| 10 | 52 (9.6%) █ | 22 (4.1%) █ |
| 11 | 54 (10.0%) █ | 0 (0.0%) |
| 12 | 28 (5.2%) █ | 19 (3.5%) █ |
| 13 | 12 (2.2%) █ | 21 (3.9%) █ |
| 14 | 0 (0.0%) | 9 (1.7%) █ |
| 15 | 10 (1.8%) █ | 0 (0.0%) |
| 16 | 13 (2.4%) █ | 21 (3.9%) █ |
| 20 | 26 (4.8%) █ | 0 (0.0%) |
| 21 | 10 (1.8%) █ | 22 (4.1%) █ |
| 22 | 9 (1.7%) █ | 0 (0.0%) |
| 24 | 10 (1.8%) █ | 10 (1.8%) █ |
| 26 | 13 (2.4%) █ | 0 (0.0%) |
| 27 | 20 (3.7%) █ | 18 (3.3%) █ |
| 28 | 0 (0.0%) | 16 (3.0%) █ |
| 30 | 14 (2.6%) █ | 0 (0.0%) |
| 31 | 0 (0.0%) | 24 (4.4%) █ |
| 33 | 8 (1.5%) █ | 0 (0.0%) |
| 34 | 0 (0.0%) | 18 (3.3%) █ |
| 35 | 18 (3.3%) █ | 0 (0.0%) |
| 36 | 29 (5.4%) █ | 15 (2.8%) █ |
| 38 | 0 (0.0%) | 13 (2.4%) █ |
| 40 | 0 (0.0%) | 7 (1.3%) █ |
| 42 | 13 (2.4%) █ | 0 (0.0%) |
| 43 | 0 (0.0%) | 15 (2.8%) █ |
| 46 | 0 (0.0%) | 18 (3.3%) █ |
| 49 | 0 (0.0%) | 12 (2.2%) █ |
| 51 | 0 (0.0%) | 10 (1.8%) █ |
| 53 | 0 (0.0%) | 7 (1.3%) █ |
| 61 | 0 (0.0%) | 11 (2.0%) █ |
| 63 | 0 (0.0%) | 10 (1.8%) █ |
| 64 | 0 (0.0%) | 12 (2.2%) █ |
| 67 | 0 (0.0%) | 10 (1.8%) █ |
| 69 | 0 (0.0%) | 10 (1.8%) █ |

##### Delete-heavy (30.0% removals)

###### Requested load factor 0.25 → remaining 0.1732

22 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 22 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 100 (90.9%) ███████████ | 100 (90.9%) ███████████ |
| 2 | 10 (9.1%) █ | 0 (0.0%) |
| 5 | 0 (0.0%) | 10 (9.1%) █ |

###### Requested load factor 0.5 → remaining 0.3543

45 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 45 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 146 (64.9%) ████████ | 147 (65.3%) ████████ |
| 2 | 10 (4.4%) █ | 18 (8.0%) █ |
| 4 | 18 (8.0%) █ | 14 (6.2%) █ |
| 6 | 6 (2.7%) █ | 19 (8.4%) █ |
| 8 | 19 (8.4%) █ | 12 (5.3%) █ |
| 9 | 18 (8.0%) █ | 0 (0.0%) |
| 11 | 8 (3.6%) █ | 0 (0.0%) |
| 27 | 0 (0.0%) | 15 (6.7%) █ |

###### Requested load factor 0.7 → remaining 0.4882

62 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 62 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 180 (58.1%) ███████ | 195 (62.9%) ████████ |
| 2 | 0 (0.0%) | 8 (2.6%) █ |
| 3 | 11 (3.5%) █ | 9 (2.9%) █ |
| 4 | 11 (3.5%) █ | 0 (0.0%) |
| 5 | 9 (2.9%) █ | 9 (2.9%) █ |
| 6 | 11 (3.5%) █ | 0 (0.0%) |
| 7 | 6 (1.9%) █ | 14 (4.5%) █ |
| 8 | 15 (4.8%) █ | 13 (4.2%) █ |
| 9 | 0 (0.0%) | 10 (3.2%) █ |
| 10 | 14 (4.5%) █ | 14 (4.5%) █ |
| 11 | 29 (9.3%) █ | 0 (0.0%) |
| 12 | 6 (1.9%) █ | 12 (3.9%) █ |
| 13 | 8 (2.6%) █ | 0 (0.0%) |
| 17 | 10 (3.2%) █ | 0 (0.0%) |
| 23 | 0 (0.0%) | 9 (2.9%) █ |
| 28 | 0 (0.0%) | 7 (2.3%) █ |
| 40 | 0 (0.0%) | 10 (3.2%) █ |

###### Requested load factor 0.85 → remaining 0.5984

76 deterministic missing-key lookup(s) per trial were issued after the workload; the table ended with 76 resident entries across 5 deterministic trial(s).

| Probes for a miss | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 1 | 233 (61.3%) ███████ | 90 (23.7%) ███ |
| 2 | 0 (0.0%) | 9 (2.4%) █ |
| 4 | 13 (3.4%) █ | 20 (5.3%) █ |
| 5 | 18 (4.7%) █ | 35 (9.2%) █ |
| 7 | 0 (0.0%) | 22 (5.8%) █ |
| 8 | 13 (3.4%) █ | 20 (5.3%) █ |
| 9 | 6 (1.6%) █ | 0 (0.0%) |
| 10 | 6 (1.6%) █ | 17 (4.5%) █ |
| 11 | 10 (2.6%) █ | 13 (3.4%) █ |
| 12 | 17 (4.5%) █ | 0 (0.0%) |
| 13 | 15 (4.0%) █ | 10 (2.6%) █ |
| 14 | 0 (0.0%) | 11 (2.9%) █ |
| 15 | 0 (0.0%) | 20 (5.3%) █ |
| 16 | 10 (2.6%) █ | 0 (0.0%) |
| 17 | 10 (2.6%) █ | 0 (0.0%) |
| 18 | 0 (0.0%) | 10 (2.6%) █ |
| 19 | 18 (4.7%) █ | 0 (0.0%) |
| 25 | 11 (2.9%) █ | 16 (4.2%) █ |
| 27 | 0 (0.0%) | 10 (2.6%) █ |
| 28 | 0 (0.0%) | 21 (5.5%) █ |
| 29 | 0 (0.0%) | 13 (3.4%) █ |
| 31 | 0 (0.0%) | 12 (3.2%) █ |
| 33 | 0 (0.0%) | 12 (3.2%) █ |
| 39 | 0 (0.0%) | 6 (1.6%) █ |
| 43 | 0 (0.0%) | 13 (3.4%) █ |


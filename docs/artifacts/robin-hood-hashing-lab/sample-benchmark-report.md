# Robin Hood hashing benchmark comparison

Deterministic benchmark report comparing Robin Hood hashing against a linear-probing baseline, now with probe-distance histograms that make dispersion visible at a glance.

- Capacity: 31
- Trials per load factor: 3
- Strategies: Robin Hood hashing, Linear probing
- Load factors: 0.25, 0.5, 0.75

## Headline comparisons

| Load factor | Entries | Lookup winner | Lookup delta vs linear | Lower probe-distance stddev | Stddev delta vs linear |
| --- | ---: | --- | ---: | --- | ---: |
| 0.25 | 8 | Tie | 0 | Tie | 0 |
| 0.5 | 16 | Tie | 0 | Robin Hood hashing | 0.0922 |
| 0.75 | 23 | Tie | 0 | Robin Hood hashing | 0.5469 |

## Aggregate metrics

| Load factor | Strategy | Avg insert probes | Avg successful lookup probes | Avg probe distance | Probe-distance stddev | Max probe distance | Max cluster length | Avg swaps |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.25 | Robin Hood hashing | 1.125 | 1.125 | 0.125 | 0.3307 | 1 | 5 | 0 |
| 0.25 | Linear probing | 1.125 | 1.125 | 0.125 | 0.3307 | 1 | 5 | 0 |
| 0.5 | Robin Hood hashing | 1.2083 | 1.2083 | 0.2083 | 0.4061 | 1 | 7 | 0.6667 |
| 0.5 | Linear probing | 1.2083 | 1.2083 | 0.2083 | 0.4983 | 2 | 7 | 0 |
| 0.75 | Robin Hood hashing | 1.8986 | 1.8986 | 0.8986 | 1.0515 | 5 | 14 | 6.6667 |
| 0.75 | Linear probing | 1.8986 | 1.8986 | 0.8986 | 1.5984 | 7 | 14 | 0 |

## Probe-distance histograms

Counts are aggregated across deterministic trials so the variance story is visible without digging through the raw CSV/JSON exports; the key thing to watch is how far each strategy spills into the longer-distance tail.

### Load factor 0.25

8 entries per trial across 3 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 21 (87.5%) ██████████ | 21 (87.5%) ██████████ |
| 1 | 3 (12.5%) ██ | 3 (12.5%) ██ |

### Load factor 0.5

16 entries per trial across 3 deterministic trial(s).

| Probe distance | Robin Hood hashing | Linear probing |
| --- | --- | --- |
| 0 | 38 (79.2%) ██████████ | 40 (83.3%) ██████████ |
| 1 | 10 (20.8%) ██ | 6 (12.5%) ██ |
| 2 | 0 (0.0%) | 2 (4.2%) █ |

### Load factor 0.75

23 entries per trial across 3 deterministic trial(s).

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


# CPU Scheduler Benchmark Pack — portfolio-batch

- family: `portfolio-batch` — classic preset stories plus deterministic generated workload families for broader scheduler comparisons
- scenarios: 6
- algorithms: SRTF, RR (q=2), MLFQ interactive (q=1/2/4, boost=8), MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- round-robin quantum: 2
- priority aging interval: 0
- context-switch cost: 1
- mlfq variant pack: portfolio
- mlfq tuning roster: MLFQ interactive (q=1/2/4, boost=8): faster boosts plus a short top quantum favor quick foreground response; MLFQ balanced (q=2/4/8, boost=12): the default queue ladder balances short-job response with moderate churn; MLFQ throughput (q=4/8/16, boost=off): longer quanta and no periodic boost reduce dispatch churn for batch-heavy mixes

## Scenario roster
| Scenario | Kind | Processes | Description | Source |
| --- | --- | ---: | --- | --- |
| convoy-mix | preset | 5 | one long CPU-bound job arrives first, then several short interactive jobs queue behind it | artifacts/cpu-scheduler-simulator/presets/convoy-mix.json |
| interactive-bursts | preset | 6 | staggered short requests compete with a background batch job, making response-time tradeoffs visible | artifacts/cpu-scheduler-simulator/presets/interactive-bursts.json |
| aging-pressure | preset | 5 | high-priority arrivals keep showing up while a low-priority batch job waits, stressing priority aging | artifacts/cpu-scheduler-simulator/presets/aging-pressure.json |
| balanced-seed-17 | generated | 6 | balanced arrivals and bursts for a neutral mixed workload baseline | generated/balanced/seed-17 |
| convoy-spike-seed-23 | generated | 6 | one heavy batch job lands beside short arrivals to stress convoy risk and dispatch overhead | generated/convoy-spike/seed-23 |
| latency-burst-seed-31 | generated | 7 | many short interactive jobs with one medium batch tail, emphasizing response-time and fairness tails | generated/latency-burst/seed-31 |

## Aggregate scoreboard
| Algorithm | Avg turnaround | Avg waiting | Avg response | Avg slowdown | Slowdown stddev | Avg overhead % | Avg throughput | Max wait seen | Max slowdown seen | Score points |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SRTF | 9.22 | 5.93 | 4.86 | 3.07 | 1.4 | 24.74 | 0.2417 | 23 | 7.0 | 31.5 |
| RR (q=2) | 14.66 | 11.38 | 5.31 | 5.52 | 2.73 | 32.12 | 0.2223 | 33 | 13.0 | 0.0 |
| MLFQ interactive (q=1/2/4, boost=8) | 17.47 | 14.18 | 3.18 | 5.62 | 1.97 | 39.16 | 0.2012 | 43 | 9.0 | 4.5 |
| MLFQ balanced (q=2/4/8, boost=12) | 13.68 | 10.4 | 3.69 | 4.58 | 1.66 | 30.12 | 0.2295 | 33 | 10.0 | 6.5 |
| MLFQ throughput (q=4/8/16, boost=off) | 12.59 | 9.3 | 5.88 | 5.09 | 2.67 | 25.11 | 0.2429 | 26 | 13.0 | 5.5 |

## Portfolio scorecards
### SRTF
- headline: wins concentrated at turnaround 6/6, waiting 6/6
- use when: best when total batch completion time matters most
- signature scenarios: convoy-mix, interactive-bursts, aging-pressure
- watch out: watch out for slower first-response time across the pack

### RR (q=2)
- headline: strongest relative showing on low overhead, response without outright pack wins
- use when: best when minimizing dispatch churn matters most
- signature scenarios: none yet
- watch out: watch out for a less even slowdown spread across processes

### MLFQ interactive (q=1/2/4, boost=8)
- headline: wins concentrated at response 5/6
- use when: best when interactive first-response speed matters most
- signature scenarios: convoy-mix, aging-pressure, balanced-seed-17
- watch out: watch out for higher queueing delay across the pack

### MLFQ balanced (q=2/4/8, boost=12)
- headline: wins concentrated at fairness 2/6, response 1/6
- use when: best when per-process fairness matters most
- signature scenarios: interactive-bursts, aging-pressure
- watch out: watch out for slower total turnaround across the pack

### MLFQ throughput (q=4/8/16, boost=off)
- headline: wins concentrated at low overhead 3/6, throughput 3/6
- use when: best when minimizing dispatch churn matters most
- signature scenarios: convoy-mix, interactive-bursts, aging-pressure
- watch out: watch out for slower first-response time across the pack

## Goal heatmap
Win rates below show how often each algorithm ties or leads that headline goal across the benchmark roster.

| Algorithm | Turnaround | Waiting | Response | Fairness | Throughput | Low overhead |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SRTF | 6/6 (100%) | 6/6 (100%) | 1/6 (16.7%) | 4/6 (66.7%) | 4/6 (66.7%) | 4/6 (66.7%) |
| RR (q=2) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) |
| MLFQ interactive (q=1/2/4, boost=8) | 0/6 (0%) | 0/6 (0%) | 5/6 (83.3%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) |
| MLFQ balanced (q=2/4/8, boost=12) | 0/6 (0%) | 0/6 (0%) | 1/6 (16.7%) | 2/6 (33.3%) | 2/6 (33.3%) | 2/6 (33.3%) |
| MLFQ throughput (q=4/8/16, boost=off) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 3/6 (50%) | 3/6 (50%) |

- screenshot artifact: `benchmark-heatmap.svg`

## Win counts
| Algorithm | Turnaround wins | Waiting wins | Response wins | Slowdown wins | Even-slowdown wins | Throughput wins | Overhead wins | Completion wins | Total wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SRTF | 6 | 6 | 1 | 5 | 4 | 4 | 4 | 4 | 34 |
| RR (q=2) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| MLFQ interactive (q=1/2/4, boost=8) | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 5 |
| MLFQ balanced (q=2/4/8, boost=12) | 0 | 0 | 1 | 1 | 2 | 2 | 2 | 2 | 10 |
| MLFQ throughput (q=4/8/16, boost=off) | 0 | 0 | 0 | 0 | 0 | 3 | 3 | 3 | 9 |

## Scenario highlights
| Scenario | Best response | Best waiting | Best fairness | Best throughput |
| --- | --- | --- | --- | --- |
| convoy-mix | MLFQ interactive (q=1/2/4, boost=8) | SRTF | SRTF | SRTF, MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off) |
| interactive-bursts | MLFQ balanced (q=2/4/8, boost=12) | SRTF | MLFQ balanced (q=2/4/8, boost=12) | MLFQ throughput (q=4/8/16, boost=off) |
| aging-pressure | SRTF, MLFQ interactive (q=1/2/4, boost=8) | SRTF | MLFQ balanced (q=2/4/8, boost=12) | MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off) |
| balanced-seed-17 | MLFQ interactive (q=1/2/4, boost=8) | SRTF | SRTF | SRTF |
| convoy-spike-seed-23 | MLFQ interactive (q=1/2/4, boost=8) | SRTF | SRTF | SRTF |
| latency-burst-seed-31 | MLFQ interactive (q=1/2/4, boost=8) | SRTF | SRTF | SRTF |
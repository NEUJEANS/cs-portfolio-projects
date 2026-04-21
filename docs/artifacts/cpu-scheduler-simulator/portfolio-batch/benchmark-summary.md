# CPU Scheduler Benchmark Pack — portfolio-batch

- family: `portfolio-batch` — classic preset stories plus deterministic generated workload families for broader scheduler comparisons
- scenarios: 6
- algorithms: FCFS, SJF, SRTF, PRIORITY (aging=2), RR (q=2), MLFQ (q=2/4/8, boost=12)
- round-robin quantum: 2
- priority aging interval: 2
- context-switch cost: 1
- mlfq quantums: 2/4/8
- mlfq boost interval: 12

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
| FCFS | 12.38 | 9.1 | 9.1 | 6.61 | 4.17 | 20.72 | 0.2563 | 23 | 19.0 | 5.5 |
| SJF | 9.81 | 6.52 | 6.52 | 4.21 | 2.26 | 20.72 | 0.2563 | 22 | 11.0 | 16.0 |
| SRTF | 9.22 | 5.93 | 4.86 | 3.07 | 1.4 | 24.74 | 0.2417 | 23 | 7.0 | 15.0 |
| PRIORITY (aging=2) | 11.11 | 7.83 | 7.83 | 5.57 | 3.43 | 20.72 | 0.2563 | 23 | 14.0 | 5.5 |
| RR (q=2) | 14.66 | 11.38 | 5.31 | 5.52 | 2.73 | 32.12 | 0.2223 | 33 | 13.0 | 0.0 |
| MLFQ (q=2/4/8, boost=12) | 13.68 | 10.4 | 3.69 | 4.58 | 1.66 | 30.12 | 0.2295 | 33 | 10.0 | 6.0 |

## Portfolio scorecards
### FCFS
- headline: wins concentrated at low overhead 6/6, throughput 6/6
- use when: best when minimizing dispatch churn matters most
- signature scenarios: convoy-mix, interactive-bursts, aging-pressure
- watch out: watch out for slower first-response time across the pack

### SJF
- headline: wins concentrated at turnaround 4/6, waiting 4/6
- use when: best when total batch completion time matters most
- signature scenarios: interactive-bursts, balanced-seed-17, convoy-spike-seed-23
- watch out: watch out for slower first-response time across the pack

### SRTF
- headline: wins concentrated at turnaround 4/6, waiting 4/6
- use when: best when total batch completion time matters most
- signature scenarios: convoy-mix, aging-pressure, convoy-spike-seed-23
- watch out: watch out for heavier context-switch overhead across the pack

### PRIORITY (aging=2)
- headline: wins concentrated at low overhead 6/6, throughput 6/6
- use when: best when minimizing dispatch churn matters most
- signature scenarios: convoy-mix, interactive-bursts, aging-pressure
- watch out: watch out for a less even slowdown spread across processes

### RR (q=2)
- headline: strongest relative showing on response, fairness without outright pack wins
- use when: best when interactive first-response speed matters most
- signature scenarios: none yet
- watch out: watch out for higher queueing delay across the pack

### MLFQ (q=2/4/8, boost=12)
- headline: wins concentrated at response 3/6, fairness 2/6
- use when: best when interactive first-response speed matters most
- signature scenarios: interactive-bursts, aging-pressure, balanced-seed-17
- watch out: watch out for heavier context-switch overhead across the pack

## Goal heatmap
Win rates below show how often each algorithm ties or leads that headline goal across the benchmark roster.

| Algorithm | Turnaround | Waiting | Response | Fairness | Throughput | Low overhead |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 6/6 (100%) | 6/6 (100%) |
| SJF | 4/6 (66.7%) | 4/6 (66.7%) | 1/6 (16.7%) | 3/6 (50%) | 6/6 (100%) | 6/6 (100%) |
| SRTF | 4/6 (66.7%) | 4/6 (66.7%) | 3/6 (50%) | 3/6 (50%) | 2/6 (33.3%) | 2/6 (33.3%) |
| PRIORITY (aging=2) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 6/6 (100%) | 6/6 (100%) |
| RR (q=2) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) |
| MLFQ (q=2/4/8, boost=12) | 0/6 (0%) | 0/6 (0%) | 3/6 (50%) | 2/6 (33.3%) | 0/6 (0%) | 0/6 (0%) |

- screenshot artifact: `benchmark-heatmap.svg`

## Win counts
| Algorithm | Turnaround wins | Waiting wins | Response wins | Slowdown wins | Even-slowdown wins | Throughput wins | Overhead wins | Completion wins | Total wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 0 | 0 | 0 | 0 | 0 | 6 | 6 | 6 | 18 |
| SJF | 4 | 4 | 1 | 3 | 3 | 6 | 6 | 6 | 33 |
| SRTF | 4 | 4 | 3 | 4 | 3 | 2 | 2 | 2 | 24 |
| PRIORITY (aging=2) | 0 | 0 | 0 | 0 | 0 | 6 | 6 | 6 | 18 |
| RR (q=2) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| MLFQ (q=2/4/8, boost=12) | 0 | 0 | 3 | 1 | 2 | 0 | 0 | 0 | 6 |

## Scenario highlights
| Scenario | Best response | Best waiting | Best fairness | Best throughput |
| --- | --- | --- | --- | --- |
| convoy-mix | SRTF | SRTF | SRTF | FCFS, SJF, PRIORITY (aging=2) |
| interactive-bursts | MLFQ (q=2/4/8, boost=12) | SJF | MLFQ (q=2/4/8, boost=12) | FCFS, SJF, PRIORITY (aging=2) |
| aging-pressure | SRTF | SRTF | MLFQ (q=2/4/8, boost=12) | FCFS, SJF, PRIORITY (aging=2) |
| balanced-seed-17 | MLFQ (q=2/4/8, boost=12) | SJF | SJF | FCFS, SJF, PRIORITY (aging=2) |
| convoy-spike-seed-23 | MLFQ (q=2/4/8, boost=12) | SJF, SRTF | SJF, SRTF | FCFS, SJF, SRTF, PRIORITY (aging=2) |
| latency-burst-seed-31 | SJF, SRTF | SJF, SRTF | SJF, SRTF | FCFS, SJF, SRTF, PRIORITY (aging=2) |
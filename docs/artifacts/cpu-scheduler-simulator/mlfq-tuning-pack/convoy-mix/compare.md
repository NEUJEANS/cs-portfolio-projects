# CPU Scheduler Comparison — convoy-mix

- preset: `convoy-mix` — one long CPU-bound job arrives first, then several short interactive jobs queue behind it
- workload source: `artifacts/cpu-scheduler-simulator/presets/convoy-mix.json`
- processes: 5
- algorithms: SRTF, RR (q=2), MLFQ interactive (q=1/2/4, boost=8), MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- round-robin quantum: 2
- priority aging interval: 0
- context-switch cost: 1
- mlfq variant pack: portfolio
- mlfq tuning roster: MLFQ interactive (q=1/2/4, boost=8): faster boosts plus a short top quantum favor quick foreground response; MLFQ balanced (q=2/4/8, boost=12): the default queue ladder balances short-job response with moderate churn; MLFQ throughput (q=4/8/16, boost=off): longer quanta and no periodic boost reduce dispatch churn for batch-heavy mixes

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SRTF | 7.6 | 4.6 | 2.4 | 11 | 75.0 | 0.25 | 25.0 | 20 |
| RR (q=2) | 9.8 | 6.8 | 4.4 | 12 | 71.43 | 0.2381 | 28.57 | 21 |
| MLFQ interactive (q=1/2/4, boost=8) | 10.6 | 7.6 | 2.0 | 14 | 65.22 | 0.2174 | 34.78 | 23 |
| MLFQ balanced (q=2/4/8, boost=12) | 8.4 | 5.4 | 3.2 | 11 | 75.0 | 0.25 | 25.0 | 20 |
| MLFQ throughput (q=4/8/16, boost=off) | 10.0 | 7.0 | 4.8 | 11 | 75.0 | 0.25 | 25.0 | 20 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| SRTF | 2.94 | 5.0 | 3.0 | 1.17 | 3.5 | P4 slowdown=5, wait=4 |
| RR (q=2) | 4.47 | 9.0 | 6.67 | 2.54 | 3.76 | P4 slowdown=9, wait=8 |
| MLFQ interactive (q=1/2/4, boost=8) | 4.11 | 6.0 | 4.0 | 1.67 | 4.84 | P5 slowdown=6, wait=10 |
| MLFQ balanced (q=2/4/8, boost=12) | 3.54 | 6.0 | 3.78 | 1.37 | 3.14 | P4 slowdown=6, wait=5 |
| MLFQ throughput (q=4/8/16, boost=off) | 4.74 | 8.0 | 5.78 | 1.93 | 2.45 | P4 slowdown=8, wait=7 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| SRTF | P1 | 11 | 0 | 20 | 2.22 |
| SRTF | P2 | 1 | 1 | 2 | 2 |
| SRTF | P3 | 2 | 2 | 4 | 2 |
| SRTF | P4 | 4 | 4 | 5 | 5 |
| SRTF | P5 | 5 | 5 | 7 | 3.5 |
| RR (q=2) | P1 | 12 | 0 | 21 | 2.33 |
| RR (q=2) | P2 | 2 | 2 | 3 | 3 |
| RR (q=2) | P3 | 3 | 3 | 5 | 2.5 |
| RR (q=2) | P4 | 8 | 8 | 9 | 9 |
| RR (q=2) | P5 | 9 | 9 | 11 | 5.5 |
| MLFQ interactive (q=1/2/4, boost=8) | P1 | 14 | 0 | 23 | 2.56 |
| MLFQ interactive (q=1/2/4, boost=8) | P2 | 1 | 1 | 2 | 2 |
| MLFQ interactive (q=1/2/4, boost=8) | P3 | 10 | 2 | 12 | 6 |
| MLFQ interactive (q=1/2/4, boost=8) | P4 | 3 | 3 | 4 | 4 |
| MLFQ interactive (q=1/2/4, boost=8) | P5 | 10 | 4 | 12 | 6 |
| MLFQ balanced (q=2/4/8, boost=12) | P1 | 11 | 0 | 20 | 2.22 |
| MLFQ balanced (q=2/4/8, boost=12) | P2 | 2 | 2 | 3 | 3 |
| MLFQ balanced (q=2/4/8, boost=12) | P3 | 3 | 3 | 5 | 2.5 |
| MLFQ balanced (q=2/4/8, boost=12) | P4 | 5 | 5 | 6 | 6 |
| MLFQ balanced (q=2/4/8, boost=12) | P5 | 6 | 6 | 8 | 4 |
| MLFQ throughput (q=4/8/16, boost=off) | P1 | 11 | 0 | 20 | 2.22 |
| MLFQ throughput (q=4/8/16, boost=off) | P2 | 4 | 4 | 5 | 5 |
| MLFQ throughput (q=4/8/16, boost=off) | P3 | 5 | 5 | 7 | 3.5 |
| MLFQ throughput (q=4/8/16, boost=off) | P4 | 7 | 7 | 8 | 8 |
| MLFQ throughput (q=4/8/16, boost=off) | P5 | 8 | 8 | 10 | 5 |

## Takeaways
- lowest average turnaround: SRTF
- lowest average waiting: SRTF
- lowest average response: MLFQ interactive (q=1/2/4, boost=8)
- lowest worst-case waiting time: SRTF, MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- lowest average slowdown: SRTF
- lowest worst slowdown: SRTF
- most even slowdown distribution: SRTF
- highest useful CPU utilization: SRTF, MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- highest throughput: SRTF, MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- lowest scheduler overhead: SRTF, MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- shortest total completion time: SRTF, MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
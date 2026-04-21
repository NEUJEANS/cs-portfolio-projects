# CPU Scheduler Comparison — aging-pressure

- preset: `aging-pressure` — high-priority arrivals keep showing up while a low-priority batch job waits, stressing priority aging
- workload source: `artifacts/cpu-scheduler-simulator/presets/aging-pressure.json`
- processes: 5
- algorithms: SRTF, RR (q=2), MLFQ interactive (q=1/2/4, boost=8), MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- round-robin quantum: 2
- priority aging interval: 0
- context-switch cost: 1
- mlfq variant pack: portfolio
- mlfq tuning roster: MLFQ interactive (q=1/2/4, boost=8): faster boosts plus a short top quantum favor quick foreground response; MLFQ balanced (q=2/4/8, boost=12): the default queue ladder balances short-job response with moderate churn; MLFQ throughput (q=4/8/16, boost=off): longer quanta and no periodic boost reduce dispatch churn for batch-heavy mixes

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SRTF | 6.6 | 4.0 | 2.8 | 11 | 68.42 | 0.2632 | 31.58 | 19 |
| RR (q=2) | 9.0 | 6.4 | 4.2 | 11 | 68.42 | 0.2632 | 31.58 | 19 |
| MLFQ interactive (q=1/2/4, boost=8) | 9.2 | 6.6 | 2.8 | 12 | 65.0 | 0.25 | 35.0 | 20 |
| MLFQ balanced (q=2/4/8, boost=12) | 7.6 | 5.0 | 3.0 | 10 | 72.22 | 0.2778 | 27.78 | 18 |
| MLFQ throughput (q=4/8/16, boost=off) | 9.2 | 6.6 | 4.6 | 10 | 72.22 | 0.2778 | 27.78 | 18 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| SRTF | 3.08 | 6.0 | 5.0 | 1.75 | 3.9 | P5 slowdown=6, wait=5 |
| RR (q=2) | 5.17 | 8.0 | 5.62 | 2.49 | 2.8 | P5 slowdown=8, wait=7 |
| MLFQ interactive (q=1/2/4, boost=8) | 4.6 | 7.0 | 4.5 | 1.66 | 3.56 | P5 slowdown=7, wait=6 |
| MLFQ balanced (q=2/4/8, boost=12) | 3.95 | 5.0 | 2.75 | 1.29 | 2.53 | P5 slowdown=5, wait=4 |
| MLFQ throughput (q=4/8/16, boost=off) | 5.35 | 7.0 | 4.75 | 2.06 | 1.74 | P5 slowdown=7, wait=6 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| SRTF | P1 | 11 | 5 | 19 | 2.38 |
| SRTF | P2 | 0 | 0 | 2 | 1 |
| SRTF | P3 | 1 | 1 | 2 | 2 |
| SRTF | P4 | 3 | 3 | 4 | 4 |
| SRTF | P5 | 5 | 5 | 6 | 6 |
| RR (q=2) | P1 | 11 | 0 | 19 | 2.38 |
| RR (q=2) | P2 | 3 | 3 | 5 | 2.5 |
| RR (q=2) | P3 | 4 | 4 | 5 | 5 |
| RR (q=2) | P4 | 7 | 7 | 8 | 8 |
| RR (q=2) | P5 | 7 | 7 | 8 | 8 |
| MLFQ interactive (q=1/2/4, boost=8) | P1 | 12 | 0 | 20 | 2.5 |
| MLFQ interactive (q=1/2/4, boost=8) | P2 | 9 | 2 | 11 | 5.5 |
| MLFQ interactive (q=1/2/4, boost=8) | P3 | 2 | 2 | 3 | 3 |
| MLFQ interactive (q=1/2/4, boost=8) | P4 | 4 | 4 | 5 | 5 |
| MLFQ interactive (q=1/2/4, boost=8) | P5 | 6 | 6 | 7 | 7 |
| MLFQ balanced (q=2/4/8, boost=12) | P1 | 10 | 0 | 18 | 2.25 |
| MLFQ balanced (q=2/4/8, boost=12) | P2 | 3 | 3 | 5 | 2.5 |
| MLFQ balanced (q=2/4/8, boost=12) | P3 | 4 | 4 | 5 | 5 |
| MLFQ balanced (q=2/4/8, boost=12) | P4 | 4 | 4 | 5 | 5 |
| MLFQ balanced (q=2/4/8, boost=12) | P5 | 4 | 4 | 5 | 5 |
| MLFQ throughput (q=4/8/16, boost=off) | P1 | 10 | 0 | 18 | 2.25 |
| MLFQ throughput (q=4/8/16, boost=off) | P2 | 5 | 5 | 7 | 3.5 |
| MLFQ throughput (q=4/8/16, boost=off) | P3 | 6 | 6 | 7 | 7 |
| MLFQ throughput (q=4/8/16, boost=off) | P4 | 6 | 6 | 7 | 7 |
| MLFQ throughput (q=4/8/16, boost=off) | P5 | 6 | 6 | 7 | 7 |

## Takeaways
- lowest average turnaround: SRTF
- lowest average waiting: SRTF
- lowest average response: SRTF, MLFQ interactive (q=1/2/4, boost=8)
- lowest worst-case waiting time: MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- lowest average slowdown: SRTF
- lowest worst slowdown: MLFQ balanced (q=2/4/8, boost=12)
- most even slowdown distribution: MLFQ balanced (q=2/4/8, boost=12)
- highest useful CPU utilization: MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- highest throughput: MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- lowest scheduler overhead: MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- shortest total completion time: MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
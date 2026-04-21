# CPU Scheduler Comparison — interactive-bursts

- preset: `interactive-bursts` — staggered short requests compete with a background batch job, making response-time tradeoffs visible
- workload source: `artifacts/cpu-scheduler-simulator/presets/interactive-bursts.json`
- processes: 6
- algorithms: SRTF, RR (q=2), MLFQ interactive (q=1/2/4, boost=8), MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- round-robin quantum: 2
- priority aging interval: 0
- context-switch cost: 1
- mlfq variant pack: portfolio
- mlfq tuning roster: MLFQ interactive (q=1/2/4, boost=8): faster boosts plus a short top quantum favor quick foreground response; MLFQ balanced (q=2/4/8, boost=12): the default queue ladder balances short-job response with moderate churn; MLFQ throughput (q=4/8/16, boost=off): longer quanta and no periodic boost reduce dispatch churn for batch-heavy mixes

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SRTF | 9.0 | 6.5 | 4.5 | 13 | 65.22 | 0.2609 | 34.78 | 23 |
| RR (q=2) | 10.17 | 7.67 | 5.67 | 13 | 65.22 | 0.2609 | 34.78 | 23 |
| MLFQ interactive (q=1/2/4, boost=8) | 12.17 | 9.67 | 3.83 | 18 | 57.69 | 0.2308 | 42.31 | 26 |
| MLFQ balanced (q=2/4/8, boost=12) | 9.17 | 6.67 | 2.67 | 17 | 65.22 | 0.2609 | 34.78 | 23 |
| MLFQ throughput (q=4/8/16, boost=off) | 9.67 | 7.17 | 4.67 | 15 | 71.43 | 0.2857 | 28.57 | 21 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| SRTF | 3.96 | 7.0 | 5.0 | 1.7 | 4.5 | P6 slowdown=7, wait=6 |
| RR (q=2) | 5.38 | 12.0 | 9.5 | 3.3 | 3.73 | P6 slowdown=12, wait=11 |
| MLFQ interactive (q=1/2/4, boost=8) | 5.33 | 9.0 | 7.0 | 2.13 | 5.91 | P6 slowdown=9, wait=8 |
| MLFQ balanced (q=2/4/8, boost=12) | 3.76 | 6.0 | 4.0 | 1.21 | 5.56 | P6 slowdown=6, wait=5 |
| MLFQ throughput (q=4/8/16, boost=off) | 5.0 | 10.0 | 7.5 | 2.53 | 3.89 | P6 slowdown=10, wait=9 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| SRTF | P1 | 12 | 0 | 18 | 3 |
| SRTF | P2 | 1 | 1 | 2 | 2 |
| SRTF | P3 | 3 | 3 | 5 | 2.5 |
| SRTF | P4 | 4 | 4 | 5 | 5 |
| SRTF | P5 | 13 | 13 | 17 | 4.25 |
| SRTF | P6 | 6 | 6 | 7 | 7 |
| RR (q=2) | P1 | 9 | 0 | 15 | 2.5 |
| RR (q=2) | P2 | 2 | 2 | 3 | 3 |
| RR (q=2) | P3 | 5 | 5 | 7 | 3.5 |
| RR (q=2) | P4 | 6 | 6 | 7 | 7 |
| RR (q=2) | P5 | 13 | 10 | 17 | 4.25 |
| RR (q=2) | P6 | 11 | 11 | 12 | 12 |
| MLFQ interactive (q=1/2/4, boost=8) | P1 | 18 | 0 | 24 | 4 |
| MLFQ interactive (q=1/2/4, boost=8) | P2 | 1 | 1 | 2 | 2 |
| MLFQ interactive (q=1/2/4, boost=8) | P3 | 10 | 3 | 12 | 6 |
| MLFQ interactive (q=1/2/4, boost=8) | P4 | 5 | 5 | 6 | 6 |
| MLFQ interactive (q=1/2/4, boost=8) | P5 | 16 | 6 | 20 | 5 |
| MLFQ interactive (q=1/2/4, boost=8) | P6 | 8 | 8 | 9 | 9 |
| MLFQ balanced (q=2/4/8, boost=12) | P1 | 17 | 0 | 23 | 3.83 |
| MLFQ balanced (q=2/4/8, boost=12) | P2 | 2 | 2 | 3 | 3 |
| MLFQ balanced (q=2/4/8, boost=12) | P3 | 2 | 2 | 4 | 2 |
| MLFQ balanced (q=2/4/8, boost=12) | P4 | 3 | 3 | 4 | 4 |
| MLFQ balanced (q=2/4/8, boost=12) | P5 | 11 | 4 | 15 | 3.75 |
| MLFQ balanced (q=2/4/8, boost=12) | P6 | 5 | 5 | 6 | 6 |
| MLFQ throughput (q=4/8/16, boost=off) | P1 | 15 | 0 | 21 | 3.5 |
| MLFQ throughput (q=4/8/16, boost=off) | P2 | 4 | 4 | 5 | 5 |
| MLFQ throughput (q=4/8/16, boost=off) | P3 | 4 | 4 | 6 | 3 |
| MLFQ throughput (q=4/8/16, boost=off) | P4 | 5 | 5 | 6 | 6 |
| MLFQ throughput (q=4/8/16, boost=off) | P5 | 6 | 6 | 10 | 2.5 |
| MLFQ throughput (q=4/8/16, boost=off) | P6 | 9 | 9 | 10 | 10 |

## Takeaways
- lowest average turnaround: SRTF
- lowest average waiting: SRTF
- lowest average response: MLFQ balanced (q=2/4/8, boost=12)
- lowest worst-case waiting time: SRTF, RR (q=2)
- lowest average slowdown: MLFQ balanced (q=2/4/8, boost=12)
- lowest worst slowdown: MLFQ balanced (q=2/4/8, boost=12)
- most even slowdown distribution: MLFQ balanced (q=2/4/8, boost=12)
- highest useful CPU utilization: MLFQ throughput (q=4/8/16, boost=off)
- highest throughput: MLFQ throughput (q=4/8/16, boost=off)
- lowest scheduler overhead: MLFQ throughput (q=4/8/16, boost=off)
- shortest total completion time: MLFQ throughput (q=4/8/16, boost=off)
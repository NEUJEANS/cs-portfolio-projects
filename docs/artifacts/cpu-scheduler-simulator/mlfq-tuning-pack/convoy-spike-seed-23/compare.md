# CPU Scheduler Comparison — convoy-spike-seed-23

- workload source: `generated/convoy-spike/seed-23`
- processes: 6
- algorithms: SRTF, RR (q=2), MLFQ interactive (q=1/2/4, boost=8), MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- round-robin quantum: 2
- priority aging interval: 0
- context-switch cost: 1
- mlfq variant pack: portfolio
- mlfq tuning roster: MLFQ interactive (q=1/2/4, boost=8): faster boosts plus a short top quantum favor quick foreground response; MLFQ balanced (q=2/4/8, boost=12): the default queue ladder balances short-job response with moderate churn; MLFQ throughput (q=4/8/16, boost=off): longer quanta and no periodic boost reduce dispatch churn for batch-heavy mixes

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SRTF | 10.17 | 6.0 | 6.0 | 18 | 83.33 | 0.2 | 16.67 | 30 |
| RR (q=2) | 21.33 | 17.17 | 7.0 | 24 | 69.44 | 0.1667 | 30.56 | 36 |
| MLFQ interactive (q=1/2/4, boost=8) | 24.33 | 20.17 | 3.83 | 29 | 60.98 | 0.1463 | 39.02 | 41 |
| MLFQ balanced (q=2/4/8, boost=12) | 18.83 | 14.67 | 4.67 | 23 | 71.43 | 0.1714 | 28.57 | 35 |
| MLFQ throughput (q=4/8/16, boost=off) | 15.17 | 11.0 | 7.83 | 19 | 80.65 | 0.1935 | 19.35 | 31 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| SRTF | 2.38 | 3.5 | 2.5 | 0.84 | 6.11 | P4 slowdown=3.5, wait=5 |
| RR (q=2) | 6.82 | 10.0 | 7.0 | 2.15 | 5.01 | P5 slowdown=10, wait=9 |
| MLFQ interactive (q=1/2/4, boost=8) | 7.17 | 9.0 | 5.58 | 1.98 | 7.82 | P4 slowdown=9, wait=16 |
| MLFQ balanced (q=2/4/8, boost=12) | 5.61 | 7.0 | 4.08 | 1.35 | 5.62 | P5 slowdown=7, wait=6 |
| MLFQ throughput (q=4/8/16, boost=off) | 5.25 | 11.0 | 8.42 | 3.28 | 4.86 | P5 slowdown=11, wait=10 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| SRTF | P1 | 18 | 18 | 30 | 2.5 |
| SRTF | P2 | 0 | 0 | 3 | 1 |
| SRTF | P3 | 3 | 3 | 6 | 2 |
| SRTF | P4 | 5 | 5 | 7 | 3.5 |
| SRTF | P5 | 1 | 1 | 2 | 2 |
| SRTF | P6 | 9 | 9 | 13 | 3.25 |
| RR (q=2) | P1 | 24 | 0 | 36 | 3 |
| RR (q=2) | P2 | 15 | 3 | 18 | 6 |
| RR (q=2) | P3 | 20 | 6 | 23 | 7.67 |
| RR (q=2) | P4 | 14 | 14 | 16 | 8 |
| RR (q=2) | P5 | 9 | 9 | 10 | 10 |
| RR (q=2) | P6 | 21 | 10 | 25 | 6.25 |
| MLFQ interactive (q=1/2/4, boost=8) | P1 | 29 | 0 | 41 | 3.42 |
| MLFQ interactive (q=1/2/4, boost=8) | P2 | 22 | 2 | 25 | 8.33 |
| MLFQ interactive (q=1/2/4, boost=8) | P3 | 24 | 3 | 27 | 9 |
| MLFQ interactive (q=1/2/4, boost=8) | P4 | 16 | 7 | 18 | 9 |
| MLFQ interactive (q=1/2/4, boost=8) | P5 | 5 | 5 | 6 | 6 |
| MLFQ interactive (q=1/2/4, boost=8) | P6 | 25 | 6 | 29 | 7.25 |
| MLFQ balanced (q=2/4/8, boost=12) | P1 | 23 | 0 | 35 | 2.92 |
| MLFQ balanced (q=2/4/8, boost=12) | P2 | 17 | 3 | 20 | 6.67 |
| MLFQ balanced (q=2/4/8, boost=12) | P3 | 16 | 3 | 19 | 6.33 |
| MLFQ balanced (q=2/4/8, boost=12) | P4 | 9 | 9 | 11 | 5.5 |
| MLFQ balanced (q=2/4/8, boost=12) | P5 | 6 | 6 | 7 | 7 |
| MLFQ balanced (q=2/4/8, boost=12) | P6 | 17 | 7 | 21 | 5.25 |
| MLFQ throughput (q=4/8/16, boost=off) | P1 | 19 | 0 | 31 | 2.58 |
| MLFQ throughput (q=4/8/16, boost=off) | P2 | 5 | 5 | 8 | 2.67 |
| MLFQ throughput (q=4/8/16, boost=off) | P3 | 6 | 6 | 9 | 3 |
| MLFQ throughput (q=4/8/16, boost=off) | P4 | 15 | 15 | 17 | 8.5 |
| MLFQ throughput (q=4/8/16, boost=off) | P5 | 10 | 10 | 11 | 11 |
| MLFQ throughput (q=4/8/16, boost=off) | P6 | 11 | 11 | 15 | 3.75 |

## Takeaways
- lowest average turnaround: SRTF
- lowest average waiting: SRTF
- lowest average response: MLFQ interactive (q=1/2/4, boost=8)
- lowest worst-case waiting time: SRTF
- lowest average slowdown: SRTF
- lowest worst slowdown: SRTF
- most even slowdown distribution: SRTF
- highest useful CPU utilization: SRTF
- highest throughput: SRTF
- lowest scheduler overhead: SRTF
- shortest total completion time: SRTF
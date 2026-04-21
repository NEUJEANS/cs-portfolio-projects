# CPU Scheduler Comparison — latency-burst-seed-31

- workload source: `generated/latency-burst/seed-31`
- processes: 7
- algorithms: SRTF, RR (q=2), MLFQ interactive (q=1/2/4, boost=8), MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- round-robin quantum: 2
- priority aging interval: 0
- context-switch cost: 1
- mlfq variant pack: portfolio
- mlfq tuning roster: MLFQ interactive (q=1/2/4, boost=8): faster boosts plus a short top quantum favor quick foreground response; MLFQ balanced (q=2/4/8, boost=12): the default queue ladder balances short-job response with moderate churn; MLFQ throughput (q=4/8/16, boost=off): longer quanta and no periodic boost reduce dispatch churn for batch-heavy mixes

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SRTF | 7.43 | 5.14 | 5.14 | 14 | 72.73 | 0.3182 | 27.27 | 22 |
| RR (q=2) | 11.0 | 8.71 | 6.43 | 17 | 64.0 | 0.28 | 36.0 | 25 |
| MLFQ interactive (q=1/2/4, boost=8) | 12.0 | 9.71 | 4.43 | 19 | 59.26 | 0.2593 | 40.74 | 27 |
| MLFQ balanced (q=2/4/8, boost=12) | 10.43 | 8.14 | 5.43 | 16 | 66.67 | 0.2917 | 33.33 | 24 |
| MLFQ throughput (q=4/8/16, boost=off) | 10.14 | 7.86 | 6.86 | 15 | 69.57 | 0.3043 | 30.43 | 23 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| SRTF | 3.62 | 6.0 | 5.0 | 1.75 | 4.19 | P4 slowdown=6, wait=5 |
| RR (q=2) | 6.59 | 13.0 | 12.0 | 4.07 | 5.26 | P4 slowdown=13, wait=12 |
| MLFQ interactive (q=1/2/4, boost=8) | 6.03 | 9.0 | 6.0 | 1.94 | 5.92 | P4 slowdown=9, wait=8 |
| MLFQ balanced (q=2/4/8, boost=12) | 5.76 | 10.0 | 9.0 | 2.93 | 5.41 | P5 slowdown=10, wait=9 |
| MLFQ throughput (q=4/8/16, boost=off) | 6.54 | 13.0 | 12.0 | 4.55 | 4.94 | P5 slowdown=13, wait=12 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| SRTF | P1 | 2 | 2 | 4 | 2 |
| SRTF | P2 | 5 | 5 | 6 | 6 |
| SRTF | P3 | 0 | 0 | 1 | 1 |
| SRTF | P4 | 5 | 5 | 6 | 6 |
| SRTF | P5 | 3 | 3 | 4 | 4 |
| SRTF | P6 | 7 | 7 | 10 | 3.33 |
| SRTF | P7 | 14 | 14 | 21 | 3 |
| RR (q=2) | P1 | 0 | 0 | 2 | 1 |
| RR (q=2) | P2 | 9 | 9 | 10 | 10 |
| RR (q=2) | P3 | 3 | 3 | 4 | 4 |
| RR (q=2) | P4 | 12 | 12 | 13 | 13 |
| RR (q=2) | P5 | 9 | 9 | 10 | 10 |
| RR (q=2) | P6 | 11 | 5 | 14 | 4.67 |
| RR (q=2) | P7 | 17 | 7 | 24 | 3.43 |
| MLFQ interactive (q=1/2/4, boost=8) | P1 | 9 | 0 | 11 | 5.5 |
| MLFQ interactive (q=1/2/4, boost=8) | P2 | 6 | 6 | 7 | 7 |
| MLFQ interactive (q=1/2/4, boost=8) | P3 | 2 | 2 | 3 | 3 |
| MLFQ interactive (q=1/2/4, boost=8) | P4 | 8 | 8 | 9 | 9 |
| MLFQ interactive (q=1/2/4, boost=8) | P5 | 6 | 6 | 7 | 7 |
| MLFQ interactive (q=1/2/4, boost=8) | P6 | 18 | 4 | 21 | 7 |
| MLFQ interactive (q=1/2/4, boost=8) | P7 | 19 | 5 | 26 | 3.71 |
| MLFQ balanced (q=2/4/8, boost=12) | P1 | 0 | 0 | 2 | 1 |
| MLFQ balanced (q=2/4/8, boost=12) | P2 | 7 | 7 | 8 | 8 |
| MLFQ balanced (q=2/4/8, boost=12) | P3 | 3 | 3 | 4 | 4 |
| MLFQ balanced (q=2/4/8, boost=12) | P4 | 7 | 7 | 8 | 8 |
| MLFQ balanced (q=2/4/8, boost=12) | P5 | 9 | 9 | 10 | 10 |
| MLFQ balanced (q=2/4/8, boost=12) | P6 | 15 | 5 | 18 | 6 |
| MLFQ balanced (q=2/4/8, boost=12) | P7 | 16 | 7 | 23 | 3.29 |
| MLFQ throughput (q=4/8/16, boost=off) | P1 | 0 | 0 | 2 | 1 |
| MLFQ throughput (q=4/8/16, boost=off) | P2 | 10 | 10 | 11 | 11 |
| MLFQ throughput (q=4/8/16, boost=off) | P3 | 3 | 3 | 4 | 4 |
| MLFQ throughput (q=4/8/16, boost=off) | P4 | 10 | 10 | 11 | 11 |
| MLFQ throughput (q=4/8/16, boost=off) | P5 | 12 | 12 | 13 | 13 |
| MLFQ throughput (q=4/8/16, boost=off) | P6 | 5 | 5 | 8 | 2.67 |
| MLFQ throughput (q=4/8/16, boost=off) | P7 | 15 | 8 | 22 | 3.14 |

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
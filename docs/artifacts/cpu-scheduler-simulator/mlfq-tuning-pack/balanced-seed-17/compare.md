# CPU Scheduler Comparison — balanced-seed-17

- workload source: `generated/balanced/seed-17`
- processes: 6
- algorithms: SRTF, RR (q=2), MLFQ interactive (q=1/2/4, boost=8), MLFQ balanced (q=2/4/8, boost=12), MLFQ throughput (q=4/8/16, boost=off)
- round-robin quantum: 2
- priority aging interval: 0
- context-switch cost: 1
- mlfq variant pack: portfolio
- mlfq tuning roster: MLFQ interactive (q=1/2/4, boost=8): faster boosts plus a short top quantum favor quick foreground response; MLFQ balanced (q=2/4/8, boost=12): the default queue ladder balances short-job response with moderate churn; MLFQ throughput (q=4/8/16, boost=off): longer quanta and no periodic boost reduce dispatch churn for batch-heavy mixes

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SRTF | 14.5 | 9.33 | 8.33 | 23 | 81.58 | 0.1579 | 13.16 | 38 |
| RR (q=2) | 26.67 | 21.5 | 4.17 | 33 | 64.58 | 0.125 | 31.25 | 48 |
| MLFQ interactive (q=1/2/4, boost=8) | 36.5 | 31.33 | 2.17 | 43 | 53.45 | 0.1034 | 43.1 | 58 |
| MLFQ balanced (q=2/4/8, boost=12) | 27.67 | 22.5 | 3.17 | 33 | 64.58 | 0.125 | 31.25 | 48 |
| MLFQ throughput (q=4/8/16, boost=off) | 21.33 | 16.17 | 6.5 | 26 | 75.61 | 0.1463 | 19.51 | 41 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| SRTF | 2.46 | 4.29 | 3.29 | 1.17 | 8.3 | P3 slowdown=4.29, wait=23 |
| RR (q=2) | 4.69 | 6.6 | 5.6 | 1.8 | 11.64 | P1 slowdown=6.6, wait=28 |
| MLFQ interactive (q=1/2/4, boost=8) | 6.46 | 8.25 | 7.25 | 2.47 | 15.02 | P2 slowdown=8.25, wait=29 |
| MLFQ balanced (q=2/4/8, boost=12) | 4.85 | 6.6 | 5.6 | 1.81 | 11.73 | P1 slowdown=6.6, wait=28 |
| MLFQ throughput (q=4/8/16, boost=off) | 3.69 | 5.8 | 4.8 | 1.66 | 10.2 | P1 slowdown=5.8, wait=24 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| SRTF | P1 | 9 | 9 | 14 | 2.8 |
| SRTF | P2 | 1 | 1 | 5 | 1.25 |
| SRTF | P3 | 23 | 23 | 30 | 4.29 |
| SRTF | P4 | 0 | 0 | 2 | 1 |
| SRTF | P5 | 17 | 17 | 24 | 3.43 |
| SRTF | P6 | 6 | 0 | 12 | 2 |
| RR (q=2) | P1 | 28 | 8 | 33 | 6.6 |
| RR (q=2) | P2 | 15 | 2 | 19 | 4.75 |
| RR (q=2) | P3 | 33 | 11 | 40 | 5.71 |
| RR (q=2) | P4 | 0 | 0 | 2 | 1 |
| RR (q=2) | P5 | 33 | 4 | 40 | 5.71 |
| RR (q=2) | P6 | 20 | 0 | 26 | 4.33 |
| MLFQ interactive (q=1/2/4, boost=8) | P1 | 32 | 4 | 37 | 7.4 |
| MLFQ interactive (q=1/2/4, boost=8) | P2 | 29 | 1 | 33 | 8.25 |
| MLFQ interactive (q=1/2/4, boost=8) | P3 | 43 | 6 | 50 | 7.14 |
| MLFQ interactive (q=1/2/4, boost=8) | P4 | 0 | 0 | 2 | 1 |
| MLFQ interactive (q=1/2/4, boost=8) | P5 | 43 | 2 | 50 | 7.14 |
| MLFQ interactive (q=1/2/4, boost=8) | P6 | 41 | 0 | 47 | 7.83 |
| MLFQ balanced (q=2/4/8, boost=12) | P1 | 28 | 5 | 33 | 6.6 |
| MLFQ balanced (q=2/4/8, boost=12) | P2 | 15 | 2 | 19 | 4.75 |
| MLFQ balanced (q=2/4/8, boost=12) | P3 | 33 | 8 | 40 | 5.71 |
| MLFQ balanced (q=2/4/8, boost=12) | P4 | 0 | 0 | 2 | 1 |
| MLFQ balanced (q=2/4/8, boost=12) | P5 | 33 | 4 | 40 | 5.71 |
| MLFQ balanced (q=2/4/8, boost=12) | P6 | 26 | 0 | 32 | 5.33 |
| MLFQ throughput (q=4/8/16, boost=off) | P1 | 24 | 11 | 29 | 5.8 |
| MLFQ throughput (q=4/8/16, boost=off) | P2 | 4 | 4 | 8 | 2 |
| MLFQ throughput (q=4/8/16, boost=off) | P3 | 26 | 16 | 33 | 4.71 |
| MLFQ throughput (q=4/8/16, boost=off) | P4 | 0 | 0 | 2 | 1 |
| MLFQ throughput (q=4/8/16, boost=off) | P5 | 22 | 8 | 29 | 4.14 |
| MLFQ throughput (q=4/8/16, boost=off) | P6 | 21 | 0 | 27 | 4.5 |

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
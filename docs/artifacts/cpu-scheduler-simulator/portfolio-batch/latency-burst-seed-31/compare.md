# CPU Scheduler Comparison — latency-burst-seed-31

- workload source: `generated/latency-burst/seed-31`
- processes: 7
- algorithms: FCFS, SJF, SRTF, PRIORITY (aging=2), RR (q=2)
- round-robin quantum: 2
- priority aging interval: 2
- context-switch cost: 1

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 10.43 | 8.14 | 8.14 | 15 | 72.73 | 0.3182 | 27.27 | 22 |
| SJF | 7.43 | 5.14 | 5.14 | 14 | 72.73 | 0.3182 | 27.27 | 22 |
| SRTF | 7.43 | 5.14 | 5.14 | 14 | 72.73 | 0.3182 | 27.27 | 22 |
| PRIORITY (aging=2) | 9.57 | 7.29 | 7.29 | 13 | 72.73 | 0.3182 | 27.27 | 22 |
| RR (q=2) | 11.0 | 8.71 | 6.43 | 17 | 64.0 | 0.28 | 36.0 | 25 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| FCFS | 7.69 | 16.0 | 15.0 | 6.13 | 5.3 | P5 slowdown=16, wait=15 |
| SJF | 3.62 | 6.0 | 5.0 | 1.75 | 4.19 | P4 slowdown=6, wait=5 |
| SRTF | 3.62 | 6.0 | 5.0 | 1.75 | 4.19 | P4 slowdown=6, wait=5 |
| PRIORITY (aging=2) | 6.59 | 14.0 | 13.0 | 5.11 | 4.62 | P4 slowdown=14, wait=13 |
| RR (q=2) | 6.59 | 13.0 | 12.0 | 4.07 | 5.26 | P4 slowdown=13, wait=12 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| FCFS | P1 | 0 | 0 | 2 | 1 |
| FCFS | P2 | 13 | 13 | 14 | 14 |
| FCFS | P3 | 3 | 3 | 4 | 4 |
| FCFS | P4 | 13 | 13 | 14 | 14 |
| FCFS | P5 | 15 | 15 | 16 | 16 |
| FCFS | P6 | 5 | 5 | 8 | 2.67 |
| FCFS | P7 | 8 | 8 | 15 | 2.14 |
| SJF | P1 | 2 | 2 | 4 | 2 |
| SJF | P2 | 5 | 5 | 6 | 6 |
| SJF | P3 | 0 | 0 | 1 | 1 |
| SJF | P4 | 5 | 5 | 6 | 6 |
| SJF | P5 | 3 | 3 | 4 | 4 |
| SJF | P6 | 7 | 7 | 10 | 3.33 |
| SJF | P7 | 14 | 14 | 21 | 3 |
| SRTF | P1 | 2 | 2 | 4 | 2 |
| SRTF | P2 | 5 | 5 | 6 | 6 |
| SRTF | P3 | 0 | 0 | 1 | 1 |
| SRTF | P4 | 5 | 5 | 6 | 6 |
| SRTF | P5 | 3 | 3 | 4 | 4 |
| SRTF | P6 | 7 | 7 | 10 | 3.33 |
| SRTF | P7 | 14 | 14 | 21 | 3 |
| PRIORITY (aging=2) | P1 | 0 | 0 | 2 | 1 |
| PRIORITY (aging=2) | P2 | 13 | 13 | 14 | 14 |
| PRIORITY (aging=2) | P3 | 3 | 3 | 4 | 4 |
| PRIORITY (aging=2) | P4 | 13 | 13 | 14 | 14 |
| PRIORITY (aging=2) | P5 | 7 | 7 | 8 | 8 |
| PRIORITY (aging=2) | P6 | 5 | 5 | 8 | 2.67 |
| PRIORITY (aging=2) | P7 | 10 | 10 | 17 | 2.43 |
| RR (q=2) | P1 | 0 | 0 | 2 | 1 |
| RR (q=2) | P2 | 9 | 9 | 10 | 10 |
| RR (q=2) | P3 | 3 | 3 | 4 | 4 |
| RR (q=2) | P4 | 12 | 12 | 13 | 13 |
| RR (q=2) | P5 | 9 | 9 | 10 | 10 |
| RR (q=2) | P6 | 11 | 5 | 14 | 4.67 |
| RR (q=2) | P7 | 17 | 7 | 24 | 3.43 |

## Takeaways
- lowest average turnaround: SJF, SRTF
- lowest average waiting: SJF, SRTF
- lowest average response: SJF, SRTF
- lowest worst-case waiting time: PRIORITY (aging=2)
- lowest average slowdown: SJF, SRTF
- lowest worst slowdown: SJF, SRTF
- most even slowdown distribution: SJF, SRTF
- highest useful CPU utilization: FCFS, SJF, SRTF, PRIORITY (aging=2)
- highest throughput: FCFS, SJF, SRTF, PRIORITY (aging=2)
- lowest scheduler overhead: FCFS, SJF, SRTF, PRIORITY (aging=2)
- shortest total completion time: FCFS, SJF, SRTF, PRIORITY (aging=2)
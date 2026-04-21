# CPU Scheduler Comparison — convoy-spike-seed-23

- workload source: `generated/convoy-spike/seed-23`
- processes: 6
- algorithms: FCFS, SJF, SRTF, PRIORITY (aging=2), RR (q=2), MLFQ (q=2/4/8, boost=12)
- round-robin quantum: 2
- priority aging interval: 2
- context-switch cost: 1
- mlfq quantums: 2/4/8
- mlfq boost interval: 12

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 18.67 | 14.5 | 14.5 | 23 | 83.33 | 0.2 | 16.67 | 30 |
| SJF | 10.17 | 6.0 | 6.0 | 18 | 83.33 | 0.2 | 16.67 | 30 |
| SRTF | 10.17 | 6.0 | 6.0 | 18 | 83.33 | 0.2 | 16.67 | 30 |
| PRIORITY (aging=2) | 13.0 | 8.83 | 8.83 | 23 | 83.33 | 0.2 | 16.67 | 30 |
| RR (q=2) | 21.33 | 17.17 | 7.0 | 24 | 69.44 | 0.1667 | 30.56 | 36 |
| MLFQ (q=2/4/8, boost=12) | 18.83 | 14.67 | 4.67 | 23 | 71.43 | 0.1714 | 28.57 | 35 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| FCFS | 8.21 | 19.0 | 18.0 | 5.88 | 7.27 | P5 slowdown=19, wait=18 |
| SJF | 2.38 | 3.5 | 2.5 | 0.84 | 6.11 | P4 slowdown=3.5, wait=5 |
| SRTF | 2.38 | 3.5 | 2.5 | 0.84 | 6.11 | P4 slowdown=3.5, wait=5 |
| PRIORITY (aging=2) | 5.01 | 12.5 | 11.5 | 4.8 | 8.19 | P4 slowdown=12.5, wait=23 |
| RR (q=2) | 6.82 | 10.0 | 7.0 | 2.15 | 5.01 | P5 slowdown=10, wait=9 |
| MLFQ (q=2/4/8, boost=12) | 5.61 | 7.0 | 4.08 | 1.35 | 5.62 | P5 slowdown=7, wait=6 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| FCFS | P1 | 0 | 0 | 12 | 1 |
| FCFS | P2 | 13 | 13 | 16 | 5.33 |
| FCFS | P3 | 14 | 14 | 17 | 5.67 |
| FCFS | P4 | 23 | 23 | 25 | 12.5 |
| FCFS | P5 | 18 | 18 | 19 | 19 |
| FCFS | P6 | 19 | 19 | 23 | 5.75 |
| SJF | P1 | 18 | 18 | 30 | 2.5 |
| SJF | P2 | 0 | 0 | 3 | 1 |
| SJF | P3 | 3 | 3 | 6 | 2 |
| SJF | P4 | 5 | 5 | 7 | 3.5 |
| SJF | P5 | 1 | 1 | 2 | 2 |
| SJF | P6 | 9 | 9 | 13 | 3.25 |
| SRTF | P1 | 18 | 18 | 30 | 2.5 |
| SRTF | P2 | 0 | 0 | 3 | 1 |
| SRTF | P3 | 3 | 3 | 6 | 2 |
| SRTF | P4 | 5 | 5 | 7 | 3.5 |
| SRTF | P5 | 1 | 1 | 2 | 2 |
| SRTF | P6 | 9 | 9 | 13 | 3.25 |
| PRIORITY (aging=2) | P1 | 15 | 15 | 27 | 2.25 |
| PRIORITY (aging=2) | P2 | 0 | 0 | 3 | 1 |
| PRIORITY (aging=2) | P3 | 1 | 1 | 4 | 1.33 |
| PRIORITY (aging=2) | P4 | 23 | 23 | 25 | 12.5 |
| PRIORITY (aging=2) | P5 | 10 | 10 | 11 | 11 |
| PRIORITY (aging=2) | P6 | 4 | 4 | 8 | 2 |
| RR (q=2) | P1 | 24 | 0 | 36 | 3 |
| RR (q=2) | P2 | 15 | 3 | 18 | 6 |
| RR (q=2) | P3 | 20 | 6 | 23 | 7.67 |
| RR (q=2) | P4 | 14 | 14 | 16 | 8 |
| RR (q=2) | P5 | 9 | 9 | 10 | 10 |
| RR (q=2) | P6 | 21 | 10 | 25 | 6.25 |
| MLFQ (q=2/4/8, boost=12) | P1 | 23 | 0 | 35 | 2.92 |
| MLFQ (q=2/4/8, boost=12) | P2 | 17 | 3 | 20 | 6.67 |
| MLFQ (q=2/4/8, boost=12) | P3 | 16 | 3 | 19 | 6.33 |
| MLFQ (q=2/4/8, boost=12) | P4 | 9 | 9 | 11 | 5.5 |
| MLFQ (q=2/4/8, boost=12) | P5 | 6 | 6 | 7 | 7 |
| MLFQ (q=2/4/8, boost=12) | P6 | 17 | 7 | 21 | 5.25 |

## Takeaways
- lowest average turnaround: SJF, SRTF
- lowest average waiting: SJF, SRTF
- lowest average response: MLFQ (q=2/4/8, boost=12)
- lowest worst-case waiting time: SJF, SRTF
- lowest average slowdown: SJF, SRTF
- lowest worst slowdown: SJF, SRTF
- most even slowdown distribution: SJF, SRTF
- highest useful CPU utilization: FCFS, SJF, SRTF, PRIORITY (aging=2)
- highest throughput: FCFS, SJF, SRTF, PRIORITY (aging=2)
- lowest scheduler overhead: FCFS, SJF, SRTF, PRIORITY (aging=2)
- shortest total completion time: FCFS, SJF, SRTF, PRIORITY (aging=2)
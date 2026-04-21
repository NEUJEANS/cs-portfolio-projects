# CPU Scheduler Comparison — balanced-seed-17

- workload source: `generated/balanced/seed-17`
- processes: 6
- algorithms: FCFS, SJF, SRTF, PRIORITY (aging=2), RR (q=2), MLFQ (q=2/4/8, boost=12)
- round-robin quantum: 2
- priority aging interval: 2
- context-switch cost: 1
- mlfq quantums: 2/4/8
- mlfq boost interval: 12

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 14.17 | 9.0 | 9.0 | 22 | 83.78 | 0.1622 | 10.81 | 37 |
| SJF | 13.83 | 8.67 | 8.67 | 22 | 83.78 | 0.1622 | 10.81 | 37 |
| SRTF | 14.5 | 9.33 | 8.33 | 23 | 81.58 | 0.1579 | 13.16 | 38 |
| PRIORITY (aging=2) | 14.17 | 9.0 | 9.0 | 22 | 83.78 | 0.1622 | 10.81 | 37 |
| RR (q=2) | 26.67 | 21.5 | 4.17 | 33 | 64.58 | 0.125 | 31.25 | 48 |
| MLFQ (q=2/4/8, boost=12) | 27.67 | 22.5 | 3.17 | 33 | 64.58 | 0.125 | 31.25 | 48 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| FCFS | 2.55 | 4.2 | 3.2 | 1.3 | 8.06 | P1 slowdown=4.2, wait=16 |
| SJF | 2.42 | 4.14 | 3.14 | 1.14 | 8.06 | P3 slowdown=4.14, wait=22 |
| SRTF | 2.46 | 4.29 | 3.29 | 1.17 | 8.3 | P3 slowdown=4.29, wait=23 |
| PRIORITY (aging=2) | 2.55 | 4.2 | 3.2 | 1.3 | 8.06 | P1 slowdown=4.2, wait=16 |
| RR (q=2) | 4.69 | 6.6 | 5.6 | 1.8 | 11.64 | P1 slowdown=6.6, wait=28 |
| MLFQ (q=2/4/8, boost=12) | 4.85 | 6.6 | 5.6 | 1.81 | 11.73 | P1 slowdown=6.6, wait=28 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| FCFS | P1 | 16 | 16 | 21 | 4.2 |
| FCFS | P2 | 6 | 6 | 10 | 2.5 |
| FCFS | P3 | 22 | 22 | 29 | 4.14 |
| FCFS | P4 | 0 | 0 | 2 | 1 |
| FCFS | P5 | 10 | 10 | 17 | 2.43 |
| FCFS | P6 | 0 | 0 | 6 | 1 |
| SJF | P1 | 8 | 8 | 13 | 2.6 |
| SJF | P2 | 6 | 6 | 10 | 2.5 |
| SJF | P3 | 22 | 22 | 29 | 4.14 |
| SJF | P4 | 0 | 0 | 2 | 1 |
| SJF | P5 | 16 | 16 | 23 | 3.29 |
| SJF | P6 | 0 | 0 | 6 | 1 |
| SRTF | P1 | 9 | 9 | 14 | 2.8 |
| SRTF | P2 | 1 | 1 | 5 | 1.25 |
| SRTF | P3 | 23 | 23 | 30 | 4.29 |
| SRTF | P4 | 0 | 0 | 2 | 1 |
| SRTF | P5 | 17 | 17 | 24 | 3.43 |
| SRTF | P6 | 6 | 0 | 12 | 2 |
| PRIORITY (aging=2) | P1 | 16 | 16 | 21 | 4.2 |
| PRIORITY (aging=2) | P2 | 6 | 6 | 10 | 2.5 |
| PRIORITY (aging=2) | P3 | 22 | 22 | 29 | 4.14 |
| PRIORITY (aging=2) | P4 | 0 | 0 | 2 | 1 |
| PRIORITY (aging=2) | P5 | 10 | 10 | 17 | 2.43 |
| PRIORITY (aging=2) | P6 | 0 | 0 | 6 | 1 |
| RR (q=2) | P1 | 28 | 8 | 33 | 6.6 |
| RR (q=2) | P2 | 15 | 2 | 19 | 4.75 |
| RR (q=2) | P3 | 33 | 11 | 40 | 5.71 |
| RR (q=2) | P4 | 0 | 0 | 2 | 1 |
| RR (q=2) | P5 | 33 | 4 | 40 | 5.71 |
| RR (q=2) | P6 | 20 | 0 | 26 | 4.33 |
| MLFQ (q=2/4/8, boost=12) | P1 | 28 | 5 | 33 | 6.6 |
| MLFQ (q=2/4/8, boost=12) | P2 | 15 | 2 | 19 | 4.75 |
| MLFQ (q=2/4/8, boost=12) | P3 | 33 | 8 | 40 | 5.71 |
| MLFQ (q=2/4/8, boost=12) | P4 | 0 | 0 | 2 | 1 |
| MLFQ (q=2/4/8, boost=12) | P5 | 33 | 4 | 40 | 5.71 |
| MLFQ (q=2/4/8, boost=12) | P6 | 26 | 0 | 32 | 5.33 |

## Takeaways
- lowest average turnaround: SJF
- lowest average waiting: SJF
- lowest average response: MLFQ (q=2/4/8, boost=12)
- lowest worst-case waiting time: FCFS, SJF, PRIORITY (aging=2)
- lowest average slowdown: SJF
- lowest worst slowdown: SJF
- most even slowdown distribution: SJF
- highest useful CPU utilization: FCFS, SJF, PRIORITY (aging=2)
- highest throughput: FCFS, SJF, PRIORITY (aging=2)
- lowest scheduler overhead: FCFS, SJF, PRIORITY (aging=2)
- shortest total completion time: FCFS, SJF, PRIORITY (aging=2)
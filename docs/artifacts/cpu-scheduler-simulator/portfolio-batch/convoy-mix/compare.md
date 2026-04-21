# CPU Scheduler Comparison — convoy-mix

- preset: `convoy-mix` — one long CPU-bound job arrives first, then several short interactive jobs queue behind it
- workload source: `artifacts/cpu-scheduler-simulator/presets/convoy-mix.json`
- processes: 5
- algorithms: FCFS, SJF, SRTF, PRIORITY (aging=2), RR (q=2), MLFQ (q=2/4/8, boost=12)
- round-robin quantum: 2
- priority aging interval: 2
- context-switch cost: 1
- mlfq quantums: 2/4/8
- mlfq boost interval: 12

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 11.8 | 8.8 | 8.8 | 13 | 78.95 | 0.2632 | 21.05 | 19 |
| SJF | 11.6 | 8.6 | 8.6 | 13 | 78.95 | 0.2632 | 21.05 | 19 |
| SRTF | 7.6 | 4.6 | 2.4 | 11 | 75.0 | 0.25 | 25.0 | 20 |
| PRIORITY (aging=2) | 11.8 | 8.8 | 8.8 | 13 | 78.95 | 0.2632 | 21.05 | 19 |
| RR (q=2) | 9.8 | 6.8 | 4.4 | 12 | 71.43 | 0.2381 | 28.57 | 21 |
| MLFQ (q=2/4/8, boost=12) | 8.4 | 5.4 | 3.2 | 11 | 75.0 | 0.25 | 25.0 | 20 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| FCFS | 7.5 | 13.0 | 12.0 | 4.02 | 4.62 | P4 slowdown=13, wait=12 |
| SJF | 7.1 | 10.0 | 9.0 | 3.29 | 4.59 | P4 slowdown=10, wait=9 |
| SRTF | 2.94 | 5.0 | 3.0 | 1.17 | 3.5 | P4 slowdown=5, wait=4 |
| PRIORITY (aging=2) | 7.5 | 13.0 | 12.0 | 4.02 | 4.62 | P4 slowdown=13, wait=12 |
| RR (q=2) | 4.47 | 9.0 | 6.67 | 2.54 | 3.76 | P4 slowdown=9, wait=8 |
| MLFQ (q=2/4/8, boost=12) | 3.54 | 6.0 | 3.78 | 1.37 | 3.14 | P4 slowdown=6, wait=5 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| FCFS | P1 | 0 | 0 | 9 | 1 |
| FCFS | P2 | 9 | 9 | 10 | 10 |
| FCFS | P3 | 10 | 10 | 12 | 6 |
| FCFS | P4 | 12 | 12 | 13 | 13 |
| FCFS | P5 | 13 | 13 | 15 | 7.5 |
| SJF | P1 | 0 | 0 | 9 | 1 |
| SJF | P2 | 9 | 9 | 10 | 10 |
| SJF | P3 | 12 | 12 | 14 | 7 |
| SJF | P4 | 9 | 9 | 10 | 10 |
| SJF | P5 | 13 | 13 | 15 | 7.5 |
| SRTF | P1 | 11 | 0 | 20 | 2.22 |
| SRTF | P2 | 1 | 1 | 2 | 2 |
| SRTF | P3 | 2 | 2 | 4 | 2 |
| SRTF | P4 | 4 | 4 | 5 | 5 |
| SRTF | P5 | 5 | 5 | 7 | 3.5 |
| PRIORITY (aging=2) | P1 | 0 | 0 | 9 | 1 |
| PRIORITY (aging=2) | P2 | 9 | 9 | 10 | 10 |
| PRIORITY (aging=2) | P3 | 10 | 10 | 12 | 6 |
| PRIORITY (aging=2) | P4 | 12 | 12 | 13 | 13 |
| PRIORITY (aging=2) | P5 | 13 | 13 | 15 | 7.5 |
| RR (q=2) | P1 | 12 | 0 | 21 | 2.33 |
| RR (q=2) | P2 | 2 | 2 | 3 | 3 |
| RR (q=2) | P3 | 3 | 3 | 5 | 2.5 |
| RR (q=2) | P4 | 8 | 8 | 9 | 9 |
| RR (q=2) | P5 | 9 | 9 | 11 | 5.5 |
| MLFQ (q=2/4/8, boost=12) | P1 | 11 | 0 | 20 | 2.22 |
| MLFQ (q=2/4/8, boost=12) | P2 | 2 | 2 | 3 | 3 |
| MLFQ (q=2/4/8, boost=12) | P3 | 3 | 3 | 5 | 2.5 |
| MLFQ (q=2/4/8, boost=12) | P4 | 5 | 5 | 6 | 6 |
| MLFQ (q=2/4/8, boost=12) | P5 | 6 | 6 | 8 | 4 |

## Takeaways
- lowest average turnaround: SRTF
- lowest average waiting: SRTF
- lowest average response: SRTF
- lowest worst-case waiting time: SRTF, MLFQ (q=2/4/8, boost=12)
- lowest average slowdown: SRTF
- lowest worst slowdown: SRTF
- most even slowdown distribution: SRTF
- highest useful CPU utilization: FCFS, SJF, PRIORITY (aging=2)
- highest throughput: FCFS, SJF, PRIORITY (aging=2)
- lowest scheduler overhead: FCFS, SJF, PRIORITY (aging=2)
- shortest total completion time: FCFS, SJF, PRIORITY (aging=2)
# CPU Scheduler Comparison — aging-pressure

- preset: `aging-pressure` — high-priority arrivals keep showing up while a low-priority batch job waits, stressing priority aging
- workload source: `artifacts/cpu-scheduler-simulator/presets/aging-pressure.json`
- processes: 5
- algorithms: FCFS, SJF, SRTF, PRIORITY (aging=2), RR (q=2)
- round-robin quantum: 2
- priority aging interval: 2
- context-switch cost: 1

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 10.4 | 7.8 | 7.8 | 10 | 76.47 | 0.2941 | 23.53 | 17 |
| SJF | 7.8 | 5.2 | 5.2 | 10 | 76.47 | 0.2941 | 23.53 | 17 |
| SRTF | 6.6 | 4.0 | 2.8 | 11 | 68.42 | 0.2632 | 31.58 | 19 |
| PRIORITY (aging=2) | 9.8 | 7.2 | 7.2 | 15 | 76.47 | 0.2941 | 23.53 | 17 |
| RR (q=2) | 9.0 | 6.4 | 4.2 | 11 | 68.42 | 0.2632 | 31.58 | 19 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| FCFS | 7.9 | 11.0 | 10.0 | 4.05 | 3.92 | P5 slowdown=11, wait=10 |
| SJF | 5.33 | 11.0 | 10.0 | 4.64 | 4.26 | P5 slowdown=11, wait=10 |
| SRTF | 3.08 | 6.0 | 5.0 | 1.75 | 3.9 | P5 slowdown=6, wait=5 |
| PRIORITY (aging=2) | 6.7 | 8.5 | 7.5 | 2.86 | 4.75 | P2 slowdown=8.5, wait=15 |
| RR (q=2) | 5.17 | 8.0 | 5.62 | 2.49 | 2.8 | P5 slowdown=8, wait=7 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| FCFS | P1 | 0 | 0 | 8 | 1 |
| FCFS | P2 | 9 | 9 | 11 | 5.5 |
| FCFS | P3 | 10 | 10 | 11 | 11 |
| FCFS | P4 | 10 | 10 | 11 | 11 |
| FCFS | P5 | 10 | 10 | 11 | 11 |
| SJF | P1 | 5 | 5 | 13 | 1.62 |
| SJF | P2 | 0 | 0 | 2 | 1 |
| SJF | P3 | 1 | 1 | 2 | 2 |
| SJF | P4 | 10 | 10 | 11 | 11 |
| SJF | P5 | 10 | 10 | 11 | 11 |
| SRTF | P1 | 11 | 5 | 19 | 2.38 |
| SRTF | P2 | 0 | 0 | 2 | 1 |
| SRTF | P3 | 1 | 1 | 2 | 2 |
| SRTF | P4 | 3 | 3 | 4 | 4 |
| SRTF | P5 | 5 | 5 | 6 | 6 |
| PRIORITY (aging=2) | P1 | 0 | 0 | 8 | 1 |
| PRIORITY (aging=2) | P2 | 15 | 15 | 17 | 8.5 |
| PRIORITY (aging=2) | P3 | 7 | 7 | 8 | 8 |
| PRIORITY (aging=2) | P4 | 7 | 7 | 8 | 8 |
| PRIORITY (aging=2) | P5 | 7 | 7 | 8 | 8 |
| RR (q=2) | P1 | 11 | 0 | 19 | 2.38 |
| RR (q=2) | P2 | 3 | 3 | 5 | 2.5 |
| RR (q=2) | P3 | 4 | 4 | 5 | 5 |
| RR (q=2) | P4 | 7 | 7 | 8 | 8 |
| RR (q=2) | P5 | 7 | 7 | 8 | 8 |

## Takeaways
- lowest average turnaround: SRTF
- lowest average waiting: SRTF
- lowest average response: SRTF
- lowest worst-case waiting time: FCFS, SJF
- lowest average slowdown: SRTF
- lowest worst slowdown: SRTF
- most even slowdown distribution: SRTF
- highest useful CPU utilization: FCFS, SJF, PRIORITY (aging=2)
- highest throughput: FCFS, SJF, PRIORITY (aging=2)
- lowest scheduler overhead: FCFS, SJF, PRIORITY (aging=2)
- shortest total completion time: FCFS, SJF, PRIORITY (aging=2)
# CPU Scheduler Comparison — interactive-bursts

- preset: `interactive-bursts` — staggered short requests compete with a background batch job, making response-time tradeoffs visible
- workload source: `artifacts/cpu-scheduler-simulator/presets/interactive-bursts.json`
- processes: 6
- algorithms: FCFS, SJF, SRTF, PRIORITY (aging=2), RR (q=2)
- round-robin quantum: 2
- priority aging interval: 2
- context-switch cost: 1

| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 8.83 | 6.33 | 6.33 | 11 | 75.0 | 0.3 | 25.0 | 20 |
| SJF | 8.0 | 5.5 | 5.5 | 10 | 75.0 | 0.3 | 25.0 | 20 |
| SRTF | 9.0 | 6.5 | 4.5 | 13 | 65.22 | 0.2609 | 34.78 | 23 |
| PRIORITY (aging=2) | 8.33 | 5.83 | 5.83 | 10 | 75.0 | 0.3 | 25.0 | 20 |
| RR (q=2) | 10.17 | 7.67 | 5.67 | 13 | 65.22 | 0.2609 | 34.78 | 23 |

## Fairness and slowdown snapshot
| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| FCFS | 5.83 | 12.0 | 11.0 | 3.62 | 3.3 | P6 slowdown=12, wait=11 |
| SJF | 4.42 | 7.0 | 6.0 | 1.92 | 3.64 | P2 slowdown=7, wait=6 |
| SRTF | 3.96 | 7.0 | 5.0 | 1.7 | 4.5 | P6 slowdown=7, wait=6 |
| PRIORITY (aging=2) | 5.08 | 8.0 | 7.0 | 2.46 | 2.97 | P4 slowdown=8, wait=7 |
| RR (q=2) | 5.38 | 12.0 | 9.5 | 3.3 | 3.73 | P6 slowdown=12, wait=11 |

## Per-process experience
| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |
| --- | --- | ---: | ---: | ---: | ---: |
| FCFS | P1 | 0 | 0 | 6 | 1 |
| FCFS | P2 | 6 | 6 | 7 | 7 |
| FCFS | P3 | 6 | 6 | 8 | 4 |
| FCFS | P4 | 7 | 7 | 8 | 8 |
| FCFS | P5 | 8 | 8 | 12 | 3 |
| FCFS | P6 | 11 | 11 | 12 | 12 |
| SJF | P1 | 0 | 0 | 6 | 1 |
| SJF | P2 | 6 | 6 | 7 | 7 |
| SJF | P3 | 10 | 10 | 12 | 6 |
| SJF | P4 | 4 | 4 | 5 | 5 |
| SJF | P5 | 10 | 10 | 14 | 3.5 |
| SJF | P6 | 3 | 3 | 4 | 4 |
| SRTF | P1 | 12 | 0 | 18 | 3 |
| SRTF | P2 | 1 | 1 | 2 | 2 |
| SRTF | P3 | 3 | 3 | 5 | 2.5 |
| SRTF | P4 | 4 | 4 | 5 | 5 |
| SRTF | P5 | 13 | 13 | 17 | 4.25 |
| SRTF | P6 | 6 | 6 | 7 | 7 |
| PRIORITY (aging=2) | P1 | 0 | 0 | 6 | 1 |
| PRIORITY (aging=2) | P2 | 6 | 6 | 7 | 7 |
| PRIORITY (aging=2) | P3 | 6 | 6 | 8 | 4 |
| PRIORITY (aging=2) | P4 | 7 | 7 | 8 | 8 |
| PRIORITY (aging=2) | P5 | 10 | 10 | 14 | 3.5 |
| PRIORITY (aging=2) | P6 | 6 | 6 | 7 | 7 |
| RR (q=2) | P1 | 9 | 0 | 15 | 2.5 |
| RR (q=2) | P2 | 2 | 2 | 3 | 3 |
| RR (q=2) | P3 | 5 | 5 | 7 | 3.5 |
| RR (q=2) | P4 | 6 | 6 | 7 | 7 |
| RR (q=2) | P5 | 13 | 10 | 17 | 4.25 |
| RR (q=2) | P6 | 11 | 11 | 12 | 12 |

## Takeaways
- lowest average turnaround: SJF
- lowest average waiting: SJF
- lowest average response: SRTF
- lowest worst-case waiting time: SJF, PRIORITY (aging=2)
- lowest average slowdown: SRTF
- lowest worst slowdown: SJF, SRTF
- most even slowdown distribution: SRTF
- highest useful CPU utilization: FCFS, SJF, PRIORITY (aging=2)
- highest throughput: FCFS, SJF, PRIORITY (aging=2)
- lowest scheduler overhead: FCFS, SJF, PRIORITY (aging=2)
- shortest total completion time: FCFS, SJF, PRIORITY (aging=2)
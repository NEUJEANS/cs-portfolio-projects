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

## Takeaways
- lowest average turnaround: SJF
- lowest average waiting: SJF
- lowest average response: SRTF
- lowest worst-case waiting time: SJF, PRIORITY (aging=2)
- highest useful CPU utilization: FCFS, SJF, PRIORITY (aging=2)
- highest throughput: FCFS, SJF, PRIORITY (aging=2)
- lowest scheduler overhead: FCFS, SJF, PRIORITY (aging=2)
- shortest total completion time: FCFS, SJF, PRIORITY (aging=2)
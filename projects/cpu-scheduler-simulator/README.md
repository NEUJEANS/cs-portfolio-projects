# cpu-scheduler-simulator

A practical operating-systems portfolio project that simulates classic CPU scheduling algorithms and reports execution timelines plus waiting/turnaround/response metrics.

## Why this project matters
- demonstrates core OS scheduling concepts in runnable code
- compares non-preemptive and preemptive strategies on the same workload
- shows deterministic simulation design and metric calculation
- includes tests and machine-readable JSON output for verification
- leaves room for stronger follow-up features like SRTF and priority scheduling

## Features
- simulate **FCFS**, **SJF (non-preemptive)**, and **Round Robin**
- load workloads from JSON
- print a readable scheduling timeline
- compute per-process completion, turnaround, waiting, and response times
- report CPU utilization and throughput
- export results as JSON
- track idle CPU time explicitly in the timeline

## Quick start
Create a workload file:

```json
[
  {"pid": "P1", "arrival": 0, "burst": 5},
  {"pid": "P2", "arrival": 1, "burst": 3},
  {"pid": "P3", "arrival": 2, "burst": 1}
]
```

Run the simulator:

```bash
python3 scheduler.py fcfs workload.json
python3 scheduler.py sjf workload.json
python3 scheduler.py rr workload.json --quantum 2
python3 scheduler.py rr workload.json --quantum 2 --json
```

## Example output
```text
Algorithm: RR (quantum=2)
Timeline:
  [0,2): P1
  [2,4): P2
  [4,5): P3
  [5,7): P1
  [7,8): P2
  [8,9): P1
```

## Test
```bash
python3 -m unittest -v test_scheduler.py
```

## Next extensions
- shortest remaining time first (SRTF)
- priority scheduling with aging
- context-switch overhead modeling
- random workload generation and chart export

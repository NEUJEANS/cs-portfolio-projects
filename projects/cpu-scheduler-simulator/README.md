# cpu-scheduler-simulator

A practical operating-systems portfolio project that simulates classic CPU scheduling algorithms and reports execution timelines plus waiting/turnaround/response metrics.

## Why this project matters
- demonstrates core OS scheduling concepts in runnable code
- compares non-preemptive and preemptive strategies on the same workload
- shows how priority aging can reduce starvation for long-waiting jobs
- shows deterministic simulation design and metric calculation
- includes tests and machine-readable JSON output for verification
- leaves room for stronger follow-up features like context-switch modeling and MLFQ comparisons

## Features
- simulate **FCFS**, **SJF (non-preemptive)**, **SRTF (preemptive shortest-remaining-time-first)**, **non-preemptive Priority scheduling**, and **Round Robin**
- load workloads from JSON
- print a readable scheduling timeline
- compute per-process completion, turnaround, waiting, and response times
- report CPU utilization and throughput
- export results as JSON
- track idle CPU time explicitly in the timeline
- accept optional per-process priority values (lower number = higher priority)
- support configurable priority aging so waiting jobs can earn better effective priority
- use deterministic tie-breaking for reproducible runs

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
python3 scheduler.py srtf workload.json
python3 scheduler.py priority workload.json --aging-interval 3
python3 scheduler.py rr workload.json --quantum 2
python3 scheduler.py srtf workload.json --json
```

Priority workloads can include an optional `priority` field. Lower numbers win, and `--aging-interval N` boosts a waiting ready job by one priority level every `N` time units.

```json
[
  {"pid": "P1", "arrival": 0, "burst": 6, "priority": 0},
  {"pid": "P2", "arrival": 0, "burst": 2, "priority": 5},
  {"pid": "P3", "arrival": 3, "burst": 1, "priority": 3}
]
```

## Example output
```text
Algorithm: SRTF
Timeline:
  [0,1): P1
  [1,2): P2
  [2,3): P3
  [3,5): P2
  [5,9): P1
```

## Test
```bash
python3 -m unittest -v test_scheduler.py
```

## Next extensions
- context-switch overhead modeling
- random workload generation and chart export
- workload presets for reproducible algorithm comparisons
- preemptive multi-level feedback queue comparisons

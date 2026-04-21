# cpu-scheduler-simulator

A practical operating-systems portfolio project that simulates classic CPU scheduling algorithms and reports execution timelines plus waiting/turnaround/response metrics.

## Why this project matters
- demonstrates core OS scheduling concepts in runnable code
- compares non-preemptive and preemptive strategies on the same workload
- shows how priority aging can reduce starvation for long-waiting jobs
- shows how context-switch overhead changes wall-clock metrics and scheduler efficiency
- shows deterministic simulation design and metric calculation
- includes tests and machine-readable JSON output for verification
- leaves room for stronger follow-up features like workload presets and MLFQ comparisons

## Features
- simulate **FCFS**, **SJF (non-preemptive)**, **SRTF (preemptive shortest-remaining-time-first)**, **non-preemptive Priority scheduling**, and **Round Robin**
- load workloads from JSON
- print a readable scheduling timeline
- compute per-process completion, turnaround, waiting, and response times
- report CPU utilization and throughput
- optionally charge a fixed `--context-switch-cost` between different runnable processes and surface scheduler-overhead metrics
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

From `projects/cpu-scheduler-simulator/`, run the simulator:

```bash
python3 scheduler.py fcfs workload.json
python3 scheduler.py sjf workload.json
python3 scheduler.py srtf workload.json
python3 scheduler.py priority workload.json --aging-interval 3
python3 scheduler.py rr workload.json --quantum 2
python3 scheduler.py rr workload.json --quantum 2 --context-switch-cost 1
python3 scheduler.py srtf workload.json --json
```

A committed demo workload for the overhead slice lives at `artifacts/cpu-scheduler-simulator/context-switch-sample.json`.

```bash
python3 scheduler.py rr ../../artifacts/cpu-scheduler-simulator/context-switch-sample.json --quantum 2 --context-switch-cost 1
```

Priority workloads can include an optional `priority` field. Lower numbers win, and `--aging-interval N` boosts a waiting ready job by one priority level every `N` time units.

When `--context-switch-cost N` is set, the simulator inserts a `CS` slice between two different runnable processes. That cost counts against wall-clock time, lowers useful CPU utilization, and is reported separately as scheduler overhead. The current model deliberately skips idle-to-process dispatches so cross-algorithm churn is easy to compare.

```json
[
  {"pid": "P1", "arrival": 0, "burst": 6, "priority": 0},
  {"pid": "P2", "arrival": 0, "burst": 2, "priority": 5},
  {"pid": "P3", "arrival": 3, "burst": 1, "priority": 3}
]
```

## Example output
```text
Algorithm: RR (quantum=2, context_switch_cost=1)
Timeline:
  [0,2): P1
  [2,3): CS
  [3,5): P2
  [5,6): CS
  [6,7): P3
```

## Test
```bash
python3 -m unittest -v test_scheduler.py
```

## Next extensions
- random workload generation and chart export
- workload presets for reproducible algorithm comparisons
- preemptive multi-level feedback queue comparisons
- side-by-side comparison dashboards for fairness vs overhead tradeoffs

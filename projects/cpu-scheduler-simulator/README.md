# cpu-scheduler-simulator

A practical operating-systems portfolio project that simulates classic CPU scheduling algorithms and reports execution timelines plus waiting/turnaround/response metrics.

## Why this project matters
- demonstrates core OS scheduling concepts in runnable code
- compares non-preemptive and preemptive strategies on the same workload
- shows how priority aging can reduce starvation for long-waiting jobs
- models a preemptive multi-level feedback queue so interactive-first scheduling tradeoffs are visible beside simpler policies
- shows how context-switch overhead changes wall-clock metrics and scheduler efficiency
- adds committed workload presets plus side-by-side comparison dashboards for fairness-vs-overhead tradeoffs
- visualizes per-process waiting and slowdown spread so fairness tradeoffs are visible, not just aggregate winners
- adds benchmark scorecards and a goal heatmap so multi-scenario results read like a portfolio case study, not just raw tables
- shows deterministic simulation design and metric calculation
- includes tests and machine-readable JSON output for verification
- leaves room for stronger follow-up features like alternate MLFQ presets and custom workload-family authoring

## Features
- simulate **FCFS**, **SJF (non-preemptive)**, **SRTF (preemptive shortest-remaining-time-first)**, **non-preemptive Priority scheduling**, **Round Robin**, and **preemptive MLFQ**
- load workloads from JSON
- print a readable scheduling timeline
- compute per-process completion, turnaround, waiting, and response times
- report CPU utilization and throughput
- optionally charge a fixed `--context-switch-cost` between different runnable processes and surface scheduler-overhead metrics
- configure MLFQ queue lengths with `--mlfq-quantums` and periodic global priority boosts with `--mlfq-boost-interval`
- compare multiple algorithms on one workload or preset and export Markdown, HTML, and JSON dashboards
- export an SVG fairness dashboard that plots per-process slowdown and waiting-time spread for each algorithm
- use committed workload presets for convoy-effect, interactive-burst, and aging-pressure demos
- run a benchmark family pack that mixes committed presets with deterministic generated workloads and exports a full multi-scenario artifact bundle
- surface benchmark scorecards plus a heatmap SVG that shows which algorithms win turnaround, waiting, response, fairness, throughput, and low-overhead goals across the pack
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
python3 scheduler.py mlfq workload.json --mlfq-quantums 2,4,8 --mlfq-boost-interval 12
python3 scheduler.py rr workload.json --quantum 2 --context-switch-cost 1
python3 scheduler.py srtf workload.json --json
python3 scheduler.py list-presets
python3 scheduler.py compare --preset interactive-bursts --quantum 2 --aging-interval 2 --mlfq-quantums 2,4,8 --mlfq-boost-interval 12 --context-switch-cost 1
python3 scheduler.py benchmark --benchmark-family portfolio-batch --quantum 2 --aging-interval 2 --mlfq-quantums 2,4,8 --mlfq-boost-interval 12 --context-switch-cost 1
```

Committed demo workloads for the project live under `artifacts/cpu-scheduler-simulator/`, including `context-switch-sample.json`, `priority-aging-sample.json`, and the preset catalog in `artifacts/cpu-scheduler-simulator/presets/`.

```bash
python3 scheduler.py rr ../../artifacts/cpu-scheduler-simulator/context-switch-sample.json --quantum 2 --context-switch-cost 1
```

Priority workloads can include an optional `priority` field. Lower numbers win, and `--aging-interval N` boosts a waiting ready job by one priority level every `N` time units.

MLFQ runs place new arrivals into the highest queue, round-robin within each queue, demote jobs that exhaust their local time allotment, and optionally reset every runnable job to the top queue every `--mlfq-boost-interval N` time units. The default queue ladder is `2,4,8`, which keeps interactive response sharp without exploding dispatch overhead.

`compare` mode runs a shared workload through multiple algorithms and highlights who wins on average turnaround, average waiting, response time, worst-case waiting, CPU utilization, throughput, scheduler overhead, and total completion time. It can print Markdown to stdout or write `--markdown-out`, `--html-out`, `--svg-out`, and `--json-out` artifacts for portfolio screenshots and repo docs. The exported metadata now also records the active MLFQ queue ladder and boost interval so recruiter-facing artifacts stay reproducible.

The comparison flow now also surfaces fairness-specific views: a slowdown snapshot table, per-process experience breakdowns, and an optional SVG artifact that makes uneven waiting and slowdown tails easy to screenshot.

`benchmark` mode goes one step wider. It runs the selected algorithms across a built-in family of preset plus deterministic generated workloads, then exports a benchmark-summary Markdown/HTML/JSON bundle, a screenshot-friendly `benchmark-heatmap.svg`, and per-scenario compare artifacts. That makes it easier to show that a scheduler recommendation holds up across multiple workload stories instead of one cherry-picked preset, including concise scorecards that explain where each scheduler shines and where it gives something up.

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
Algorithm: MLFQ (quantums=2/4/8, boost_interval=12, context_switch_cost=1)
Timeline:
  [0,2): P1
  [2,3): CS
  [3,4): P2
  [4,5): CS
  [5,7): P1
```

## Comparison artifact example
```bash
python3 scheduler.py compare \
  --preset interactive-bursts \
  --quantum 2 \
  --aging-interval 2 \
  --mlfq-quantums 2,4,8 \
  --mlfq-boost-interval 12 \
  --context-switch-cost 1 \
  --markdown-out ../../docs/artifacts/cpu-scheduler-simulator/interactive-bursts-compare.md \
  --html-out ../../docs/artifacts/cpu-scheduler-simulator/interactive-bursts-compare.html \
  --svg-out ../../docs/artifacts/cpu-scheduler-simulator/interactive-bursts-compare-fairness.svg \
  --json-out ../../docs/artifacts/cpu-scheduler-simulator/interactive-bursts-compare.json

python3 scheduler.py benchmark \
  --benchmark-family portfolio-batch \
  --quantum 2 \
  --aging-interval 2 \
  --mlfq-quantums 2,4,8 \
  --mlfq-boost-interval 12 \
  --context-switch-cost 1 \
  --output-dir ../../docs/artifacts/cpu-scheduler-simulator/portfolio-batch
```

The committed benchmark bundle now lives under `docs/artifacts/cpu-scheduler-simulator/portfolio-batch/` and includes a pack-level summary, `benchmark-heatmap.svg`, per-scenario compare Markdown/HTML/SVG/JSON artifacts, and reproducible workload JSON snapshots.

## Test
```bash
python3 -m unittest -v test_scheduler.py
```

## Next extensions
- alternate MLFQ presets that model more queues or stricter boost cadence
- arrival-pattern editors for custom workload-family authoring

# Disk Scheduler Lab

A compact operating-systems portfolio lab that simulates classic disk scheduling algorithms and compares their seek costs.

## Features
- FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK scheduling
- JSON input payloads or inline CLI request lists
- explicit head path output, including SCAN/C-SCAN boundary sweeps and LOOK/C-LOOK turnaround jumps
- comparison mode for quick algorithm tradeoff analysis across multiple policies
- focused unittest coverage for algorithm behavior, corner cases, and CLI output

## Why it is portfolio-worthy
This project shows OS scheduling intuition, tradeoff reasoning, CLI design, JSON-driven inputs, and testable algorithm implementations in a format that is easy to demo during interviews.

## Usage

### Simulate one algorithm
```bash
python3 projects/disk-scheduler-lab/disk_scheduler.py \
  simulate \
  --input projects/disk-scheduler-lab/sample_requests.json \
  --algorithm look
```

### Compare multiple algorithms
```bash
python3 projects/disk-scheduler-lab/disk_scheduler.py \
  compare \
  --start 50 \
  --max-cylinder 199 \
  --direction up \
  --requests 82 170 43 140 24 16 190 \
  --algorithms fcfs sstf scan cscan look clook
```

## Output shape
```json
{
  "algorithm": "look",
  "service_order": [82, 140, 170, 190, 43, 24, 16],
  "path": [50, 82, 140, 170, 190, 43, 24, 16],
  "total_head_movement": 314,
  "average_seek": 44.86
}
```

## Tradeoffs
- **FCFS** is simple and fair by arrival order but can cause large seek overhead.
- **SSTF** reduces movement greedily but may starve far-away requests.
- **SCAN** models the elevator approach and balances throughput with predictable boundary sweeps.
- **C-SCAN** offers more uniform wait times at the cost of full wraparound travel.
- **LOOK** trims wasted boundary movement by reversing at the furthest pending request instead of the physical end.
- **C-LOOK** keeps circular fairness while also avoiding unnecessary trips to cylinder `0` or `max_cylinder`.

## Run tests
```bash
python3 -m unittest -v projects/disk-scheduler-lab/test_disk_scheduler.py
```

## Future improvements
- model arrival times so the lab can simulate online request streams
- export comparison tables or charts for README/report generation
- add request-deadline or starvation metrics for fairness analysis

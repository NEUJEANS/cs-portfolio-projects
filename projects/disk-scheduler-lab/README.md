# Disk Scheduler Lab

A compact operating-systems portfolio lab that simulates classic disk scheduling algorithms and compares their seek costs.

## Features
- FCFS, SSTF, SCAN, and C-SCAN scheduling
- JSON input payloads or inline CLI request lists
- explicit head path output, including SCAN/C-SCAN boundary sweeps
- comparison mode for quick algorithm tradeoff analysis
- focused pytest coverage for algorithm behavior and CLI output

## Why it is portfolio-worthy
This project shows OS scheduling intuition, tradeoff reasoning, CLI design, JSON-driven inputs, and testable algorithm implementations in a format that is easy to demo during interviews.

## Usage

### Simulate one algorithm
```bash
python projects/disk-scheduler-lab/disk_scheduler.py \
  --input projects/disk-scheduler-lab/sample_requests.json \
  simulate --algorithm scan
```

### Compare multiple algorithms
```bash
python projects/disk-scheduler-lab/disk_scheduler.py \
  --start 50 \
  --max-cylinder 199 \
  --direction up \
  --requests 82 170 43 140 24 16 190 \
  compare --algorithms fcfs sstf scan cscan
```

## Output shape
```json
{
  "algorithm": "scan",
  "service_order": [82, 140, 170, 190, 43, 24, 16],
  "path": [50, 82, 140, 170, 190, 199, 43, 24, 16],
  "total_head_movement": 332,
  "average_seek": 47.43
}
```

## Tradeoffs
- **FCFS** is simple and fair by arrival order but can cause large seek overhead.
- **SSTF** reduces movement greedily but may starve far-away requests.
- **SCAN** models the elevator approach and balances throughput with predictability.
- **C-SCAN** offers more uniform wait times at the cost of wraparound travel.

## Run tests
```bash
python3 -m unittest projects/disk-scheduler-lab/test_disk_scheduler.py
```

## Future improvements
- add LOOK and C-LOOK variants for non-boundary sweeps
- model arrival times so the lab can simulate online request streams
- export comparison tables or charts for README/report generation

# task-tracker-cli

## Overview
Track tasks with JSON persistence, priorities, and completion workflow.

## Stack
- Python
- no extra runtime dependency required for the default path

## Features
- focused scope suitable for a CS student portfolio
- runnable locally from the command line
- core behavior covered by tests
- clear v2 expansion path

## Usage
```bash
python3 task_tracker.py --storage tasks.json add "finish OS assignment" --priority high
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- richer validation and edge-case handling
- packaging / release automation
- more integration or end-to-end tests

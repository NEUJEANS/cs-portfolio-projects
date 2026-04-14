# library-manager-sqlite

## Overview
Manage books and checkout state with SQLite persistence.

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
python3 library_manager.py --db library.db add "Clean Code" "Robert C. Martin"
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- richer validation and edge-case handling
- packaging / release automation
- more integration or end-to-end tests

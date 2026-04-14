# file-integrity-monitor

## Overview
Snapshot a directory tree with hashing metadata, save a reusable baseline manifest, and compare the current state against that baseline.

## Why it is portfolio-worthy
- demonstrates recursive filesystem traversal and content hashing
- shows clean CLI design with reusable manifests and ignore patterns
- includes automated tests that exercise both library and command-line usage
- maps well to real-world integrity monitoring, deployment checks, and backup verification

## Stack
- Python 3 standard library only

## Features
- create versioned baseline manifests with file hashes, sizes, and modification timestamps
- diff a current directory snapshot against a saved baseline
- ignore temporary or generated files with repeatable glob patterns
- emit either JSON for tooling or a readable text summary for humans
- keep the core logic importable for reuse in other scripts

## Usage
Create a baseline manifest:

```bash
python3 integrity_monitor.py scan ../task-tracker-cli \
  --ignore "*.db" \
  --ignore "*.tmp" \
  --output baseline.json
```

Print a human-readable diff later:

```bash
python3 integrity_monitor.py diff ../task-tracker-cli \
  --baseline baseline.json \
  --format text
```

Emit JSON for automation:

```bash
python3 integrity_monitor.py diff ../task-tracker-cli \
  --baseline baseline.json \
  --format json
```

Fail a CI job when unexpected changes are found:

```bash
python3 integrity_monitor.py diff ../task-tracker-cli \
  --baseline baseline.json \
  --format text \
  --fail-on-changes
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- support directory-level include rules in addition to ignore globs
- add exit codes for CI workflows when changes are detected
- optionally sign manifests for tamper-evident verification

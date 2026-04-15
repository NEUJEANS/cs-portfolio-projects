# file-integrity-monitor

## Overview
Snapshot a directory tree with hashing metadata, save a reusable baseline manifest, and compare the current state against that baseline.

## Why it is portfolio-worthy
- demonstrates recursive filesystem traversal and content hashing
- shows clean CLI design with reusable manifests, ignore patterns, and tamper-evident signed baselines
- includes automated tests that exercise both library and command-line usage
- maps well to real-world integrity monitoring, deployment checks, and backup verification

## Stack
- Python 3 standard library only

## Features
- create versioned baseline manifests with file hashes, sizes, and modification timestamps
- diff a current directory snapshot against a saved baseline
- ignore temporary or generated files with repeatable glob patterns
- emit either JSON for tooling or a readable text summary for humans
- sign manifests with an HMAC secret and verify them before trusting a baseline
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

Create and verify a tamper-evident signed baseline:

```bash
export INTEGRITY_MONITOR_SECRET="replace-with-a-long-random-secret"
python3 integrity_monitor.py scan ../task-tracker-cli \
  --output signed-baseline.json \
  --signing-key-env INTEGRITY_MONITOR_SECRET

python3 integrity_monitor.py verify ../task-tracker-cli \
  --baseline signed-baseline.json \
  --signing-key-env INTEGRITY_MONITOR_SECRET

python3 integrity_monitor.py diff ../task-tracker-cli \
  --baseline signed-baseline.json \
  --signing-key-env INTEGRITY_MONITOR_SECRET \
  --format text
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- support directory-level include rules in addition to ignore globs
- optionally rotate or load signing secrets from a dedicated secrets manager

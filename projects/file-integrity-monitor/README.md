# file-integrity-monitor

## Overview
Snapshot a directory tree with hashing metadata, save a reusable baseline manifest, and compare the current state against that baseline.

## Why it is portfolio-worthy
- demonstrates recursive filesystem traversal and content hashing
- shows clean CLI design with reusable manifests, ignore patterns, tamper-evident signed baselines, and rotation-friendly verification workflows
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
- embed a key identifier in signed manifests so rotated secrets can be accepted during cutovers
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

Support a key-rotation window while keeping old signed baselines valid:

```bash
export INTEGRITY_SECRET_V1="legacy-secret"
export INTEGRITY_SECRET_V2="new-secret"
python3 integrity_monitor.py scan ../task-tracker-cli \
  --output signed-baseline-v1.json \
  --signing-key-env INTEGRITY_SECRET_V1 \
  --key-id INTEGRITY_SECRET_V1

python3 integrity_monitor.py verify ../task-tracker-cli \
  --baseline signed-baseline-v1.json \
  --verify-key-env INTEGRITY_SECRET_V2 \
  --verify-key-env INTEGRITY_SECRET_V1
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- support asymmetric signing and verification with public/private key material
- optionally load rotation candidates from a dedicated secrets manager or KMS

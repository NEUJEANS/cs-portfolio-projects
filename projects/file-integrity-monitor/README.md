# file-integrity-monitor

## Overview
Snapshot a directory tree with hashing metadata, save a reusable baseline manifest, and compare the current state against that baseline.

## Why it is portfolio-worthy
- demonstrates recursive filesystem traversal and content hashing
- shows clean CLI design with reusable manifests, ignore patterns, tamper-evident signed baselines, and rotation-friendly verification workflows
- includes both symmetric and asymmetric trust models without breaking backward compatibility
- includes automated tests that exercise both library and command-line usage
- maps well to real-world integrity monitoring, deployment checks, and backup verification

## Stack
- Python 3 standard library
- optional system `openssl` binary for asymmetric signing and verification

## Features
- create versioned baseline manifests with file hashes, sizes, and modification timestamps
- diff a current directory snapshot against a saved baseline
- ignore temporary or generated files with repeatable glob patterns
- emit either JSON for tooling or a readable text summary for humans
- sign manifests with an HMAC secret and verify them before trusting a baseline
- sign manifests with a PEM private key and verify them with matching public keys via OpenSSL
- embed a key identifier in signed manifests so rotated secrets or public keys can be accepted during cutovers
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

Use asymmetric signing when you want public verification without sharing the signing secret:

```bash
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out integrity-private.pem
openssl rsa -pubout -in integrity-private.pem -out integrity-public.pem

export INTEGRITY_PRIVATE_KEY="$PWD/integrity-private.pem"
export INTEGRITY_PUBLIC_V1="$PWD/integrity-public.pem"

python3 integrity_monitor.py scan ../task-tracker-cli \
  --output signed-baseline-rsa.json \
  --private-key-env INTEGRITY_PRIVATE_KEY \
  --key-id INTEGRITY_PUBLIC_V1

python3 integrity_monitor.py verify ../task-tracker-cli \
  --baseline signed-baseline-rsa.json \
  --public-key-env INTEGRITY_PUBLIC_V1
```

Accept multiple public keys during a rotation window:

```bash
export INTEGRITY_PUBLIC_V1="$PWD/old-public.pem"
export INTEGRITY_PUBLIC_V2="$PWD/new-public.pem"

python3 integrity_monitor.py diff ../task-tracker-cli \
  --baseline signed-baseline-rsa.json \
  --public-key-env INTEGRITY_PUBLIC_V2 \
  --public-key-env INTEGRITY_PUBLIC_V1 \
  --format text
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- support Ed25519-style signing flows without depending on the OpenSSL CLI shape
- optionally load rotation candidates from a dedicated secrets manager or KMS

# shamir-secret-sharing-lab

A portfolio-ready Python lab that implements Shamir's Secret Sharing for UTF-8 secrets using finite-field polynomial interpolation over GF(257).

## Why it is interesting
- demonstrates threshold cryptography in a compact, interview-friendly project
- shows practical finite-field math, Horner polynomial evaluation, and Lagrange interpolation
- produces resumable JSON share bundles that make demos easy to repeat locally
- optionally authenticates share bundles with a PBKDF2-derived HMAC so tampering is detected before recovery
- gives you a clean story about avoiding single points of failure for credentials, recovery codes, or team-owned secrets

## Features
- split a UTF-8 secret into `n` shares with a `k`-of-`n` recovery threshold
- recover the secret from any valid subset of shares meeting the threshold
- inspect share bundles to understand threshold, ids, and payload size
- optionally authenticate a share bundle with a passphrase-derived HMAC tag
- deterministic validation for malformed bundles, missing passphrases, and insufficient-share recovery attempts
- unit tests and CLI workflow tests for portfolio-ready confidence

## Usage

Split a secret into shares:

```bash
python3 shamir_secret_sharing_lab.py split \
  --secret "launch codes stay local" \
  --threshold 3 \
  --shares 5 \
  --output artifacts/shares.json
```

Split a secret into authenticated shares:

```bash
python3 shamir_secret_sharing_lab.py split \
  --secret "launch codes stay local" \
  --threshold 3 \
  --shares 5 \
  --output artifacts/shares.json \
  --auth-passphrase "demo-bundle-passphrase"
```

Inspect the bundle:

```bash
python3 shamir_secret_sharing_lab.py inspect \
  --input artifacts/shares.json
```

Inspect and verify the authentication tag:

```bash
python3 shamir_secret_sharing_lab.py inspect \
  --input artifacts/shares.json \
  --auth-passphrase "demo-bundle-passphrase"
```

Recover the secret from any threshold-satisfying subset:

```bash
python3 shamir_secret_sharing_lab.py recover \
  --input artifacts/shares.json \
  --use 1 3 5
```

Recover an authenticated bundle:

```bash
python3 shamir_secret_sharing_lab.py recover \
  --input artifacts/shares.json \
  --use 1 3 5 \
  --auth-passphrase "demo-bundle-passphrase"
```

## Test

```bash
python3 -m unittest tests/test_shamir_secret_sharing_lab.py
```

## Future improvements
- support binary file secrets in addition to UTF-8 text secrets
- add visualization output that shows interpolation basis terms for teaching demos
- add per-share signatures for multi-party authenticity instead of shared-passphrase bundle authentication

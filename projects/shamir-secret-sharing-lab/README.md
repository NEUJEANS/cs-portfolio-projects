# shamir-secret-sharing-lab

A portfolio-ready Python lab that implements Shamir's Secret Sharing for UTF-8 secrets using finite-field polynomial interpolation over GF(257).

## Why it is interesting
- demonstrates threshold cryptography in a compact, interview-friendly project
- shows practical finite-field math, Horner polynomial evaluation, and Lagrange interpolation
- produces resumable JSON share bundles that make demos easy to repeat locally
- gives you a clean story about avoiding single points of failure for credentials, recovery codes, or team-owned secrets

## Features
- split a UTF-8 secret into `n` shares with a `k`-of-`n` recovery threshold
- recover the secret from any valid subset of shares meeting the threshold
- inspect share bundles to understand threshold, ids, and payload size
- deterministic validation for malformed bundles and insufficient-share recovery attempts
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

Inspect the bundle:

```bash
python3 shamir_secret_sharing_lab.py inspect \
  --input artifacts/shares.json
```

Recover the secret from any threshold-satisfying subset:

```bash
python3 shamir_secret_sharing_lab.py recover \
  --input artifacts/shares.json \
  --use 1 3 5
```

## Test

```bash
python3 -m unittest tests/test_shamir_secret_sharing_lab.py
```

## Future improvements
- add optional authenticated shares with MACs or signatures to detect tampering explicitly
- support binary file secrets in addition to UTF-8 text secrets
- add visualization output that shows interpolation basis terms for teaching demos

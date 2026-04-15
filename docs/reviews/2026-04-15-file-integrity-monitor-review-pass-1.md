# File Integrity Monitor Review Pass 1 — 2026-04-15

## Focus
Signed baseline workflow and correctness of canonical HMAC verification.

## Findings
1. Signed baseline verification flow worked with the correct secret.
2. Wrong-secret verification returned the dedicated signature failure exit code.
3. Baseline files stored inside the scanned tree originally appeared as false-positive additions during diff.

## Action
- Fixed the embedded-baseline false positive by tracking `embedded_paths` in manifests and excluding those files from live snapshots.

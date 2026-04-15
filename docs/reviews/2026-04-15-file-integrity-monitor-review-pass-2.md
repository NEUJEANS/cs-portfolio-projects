# File Integrity Monitor Review Pass 2 — 2026-04-15

## Focus
CLI ergonomics, usage errors, and regression coverage.

## Checks
- Verified `diff` requires `--signing-key-env` when a baseline is signed.
- Verified `verify` requires both a signed baseline and a signing key env var.
- Confirmed new tests cover signed scan/diff/verify flows plus embedded baseline handling.

## Findings
- No additional code fixes required after the new regression tests passed.

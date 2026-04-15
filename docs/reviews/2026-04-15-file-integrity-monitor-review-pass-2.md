# File Integrity Monitor Review Pass 2 — 2026-04-15

## Focus
CLI ergonomics and failure-mode review.

## Findings
- `--verify-key-env` needs to be repeatable so operators can validate during cutovers.
- Error messaging should explicitly mention either `--signing-key-env` or `--verify-key-env` for signed-baseline verification flows.
- This is now reflected in the CLI usage checks and tests.

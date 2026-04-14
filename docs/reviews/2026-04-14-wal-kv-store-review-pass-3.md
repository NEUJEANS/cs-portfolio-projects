# WAL KV Store Review Pass 3

## Focus
Regression coverage.

## Issues found
1. Tests did not explicitly verify post-checkpoint history reset.
2. CLI tests did not verify the new `existed` delete field.

## Fixes applied
- Added assertions for empty history after checkpoint.
- Added CLI assertion covering the `existed` field on delete.

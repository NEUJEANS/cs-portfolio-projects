# 2026-04-15 — shamir-secret-sharing-lab review pass 2

## Focus
CLI input validation and recovery correctness.

## Issue found
- `recover --use` accepted duplicate share ids, which could make a bad invocation look like it used enough shares when it actually repeated one id.

## Fix applied
- Added an explicit distinct-id check in `recover_command`.
- Preserved the existing threshold enforcement in `recover_secret`.

# File Integrity Monitor Key Rotation Refresh — 2026-04-15

## Goal
Add a practical follow-up to signed manifests without pulling in non-stdlib crypto dependencies.

## Refresher
- HMAC is symmetric, so true asymmetric verification is out of scope without new crypto tooling.
- A realistic intermediate step is a key-rotation workflow:
  - sign a manifest with one secret
  - embed a stable key identifier in signature metadata
  - allow verification against a small set of accepted secrets during rotation windows
  - prefer matching the declared key identifier before testing other candidates

## Self-test
- Q: Why store `key_id` if the manifest already has a signature?
  - A: So operators can identify which secret should verify the manifest and support staged key rotation without guessing.
- Q: Why keep multiple `--verify-key-env` flags instead of just one?
  - A: To let old baselines remain valid while infrastructure rolls to a new secret.
- Q: Why not claim asymmetric signing support yet?
  - A: The project is stdlib-only and Python's stdlib does not provide a practical public/private signature implementation for this CLI.

## Implementation direction chosen
Add `--key-id` and repeatable `--verify-key-env`, surface the matched verification env in `verify` output, and cover the rotation path with CLI tests.

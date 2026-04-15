# File Integrity Monitor Signing Refresh — 2026-04-15

## Goal
Add tamper-evident manifest signing without pulling in third-party crypto packages.

## Refresher Notes
- HMAC-SHA256 is a good fit for shared-secret integrity verification in a standard-library-only project.
- Sign a canonical serialization, not a pretty-printed JSON string, so field order and whitespace do not break verification.
- Verification should happen before trusting a saved baseline for diffing.
- If the baseline file lives inside the scanned directory, it must be excluded from the live snapshot or every diff will report a false positive.

## Self-test
- Built a signed manifest and verified it with the correct secret.
- Confirmed verification fails with the wrong secret.
- Confirmed a baseline stored inside the scanned directory is auto-excluded from subsequent diffs.

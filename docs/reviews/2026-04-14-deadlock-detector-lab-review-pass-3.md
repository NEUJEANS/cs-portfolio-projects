# deadlock-detector-lab review pass 3

## Focus
Edge cases and determinism.

## Checks
- inspected resource/process ordering for deterministic JSON output
- reviewed validation for negative counts and malformed payloads
- re-ran the unittest suite after the error-handling fix

## Findings
1. Stable ordering keeps tests and diffs predictable.
2. Validation covers the main malformed-input cases needed for a student portfolio slice.
3. Current scope is intentionally compact but meaningful and resumable.

## Fixes made
- no further fixes required after verification

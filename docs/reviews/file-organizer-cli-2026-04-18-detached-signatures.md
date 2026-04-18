# file-organizer-cli review log — 2026-04-18 detached-signature slice

## Scope
Added detached manifest signatures, undo-time signature verification, README/demo updates, and regression coverage for checksum-backed authorship proof.

## Review pass 1 — test realism / key handling
- Checked the new detached-signature tests against a real organize run.
- Issue found: the test helper wrote signing keys into the same root directory being organized, so the organizer moved those key files before the signing step and the signature tests failed with `ENOENT`.
- Fix applied: updated the test helper to place generated keys under a dedicated `keys/` subdirectory so the non-recursive organize pass leaves them in place.

## Review pass 2 — CLI safety guard
- Checked the new signing flags for guard-rail consistency.
- Issue found: `--sign-manifest` could be used without `--manifest-checksum`, which weakened the intended “integrity + authorship” workflow.
- Fix applied: required checksum-backed manifests before detached signing both in the CLI argument validation and in the signing helper itself, then added regression coverage for the precondition.

## Review pass 3 — README / artifact bundle alignment
- Compared the refreshed README and generated demo bundle against the shipped signature flow.
- Issue found: the docs/demo summary still described only checksum-backed manifests and omitted the new detached-signature sidecar, public key, and verification proof artifacts.
- Fix applied: updated the README usage/examples plus the generated demo-summary bundle list so the published portfolio walkthrough matches the shipped signature workflow.

## Validation rerun after fixes
- `npm test --prefix projects/file-organizer-cli`
- `npm run demo:artifacts --prefix projects/file-organizer-cli`
- `git diff --check`
- real temp-dir smoke: sign a checksum-backed manifest with `--sign-manifest`, verify/undo with `--verify-manifest-signature`, and confirm the detached sidecar plus restored files exist

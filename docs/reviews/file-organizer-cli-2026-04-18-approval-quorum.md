# file-organizer-cli approval-quorum review log

## Review pass 1 — regression sweep
- Ran `npm test --prefix projects/file-organizer-cli`.
- Ran `npm run demo:artifacts --prefix projects/file-organizer-cli`.
- Ran `git diff --check`.
- Result: the multi-signer approval + quorum implementation, updated demo bundle, and report formatting all passed before deeper CLI review.

## Review pass 2 — CLI/docs consistency audit
- Reviewed the README usage examples, help text, and the new multi-signer workflow claims side by side.
- Found a real product gap: the README said a second `--sign-manifest` run could append another approval, but the CLI parser only allowed `--sign-manifest` during an organize run with `--manifest-out`.
- Fixes shipped:
  - added a dedicated CLI mode that signs an existing manifest when the manifest path is passed positionally with `--sign-manifest`
  - added a text report for `manifest-signature` actions
  - updated help output, README usage examples, and checklist notes to document the existing-manifest signing flow

## Review pass 3 — real CLI smoke for two-step approval append
- Created an isolated temp workflow with:
  - a checksum-backed manifest
  - two Ed25519 reviewer keys
  - a signer policy requiring both `organize-approver` and `undo-approver`
- Ran:
  - `node projects/file-organizer-cli/organizer.js "$tmpdir/downloads" --config "$tmpdir/buckets.json" --manifest-out "$tmpdir/runs/latest.json" --manifest-checksum`
  - `node projects/file-organizer-cli/organizer.js "$tmpdir/runs/latest.json" --sign-manifest "$tmpdir/keys/organize.pem" --signature-path "$tmpdir/runs/latest.json.sig.json" --signer-policy "$tmpdir/keys/trusted-signers.json"`
  - `node projects/file-organizer-cli/organizer.js "$tmpdir/runs/latest.json" --sign-manifest "$tmpdir/keys/undo.pem" --signature-path "$tmpdir/runs/latest.json.sig.json" --signer-policy "$tmpdir/keys/trusted-signers.json"`
  - `node projects/file-organizer-cli/organizer.js --undo "$tmpdir/runs/latest.json" --signature-path "$tmpdir/runs/latest.json.sig.json" --signer-policy "$tmpdir/keys/trusted-signers.json"`
- Verified:
  - sequential CLI signing appends approvals onto the same sidecar bundle
  - signer-policy quorum reaches 2/2 trusted approvals after the second append
  - policy-only undo verification succeeds and restores the original files

## Extra test hardening
- Added an automated CLI integration test that signs the same manifest twice through the real executable and then verifies the resulting quorum bundle.
- While adding that test, replaced `node:child_process/promises` with `util.promisify(child_process.execFile)` for compatibility with the runtime available in this repo.
